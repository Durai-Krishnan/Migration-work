import json
import sys
from datetime import datetime
import uuid
from dateutil import parser
from dateutil.relativedelta import relativedelta


def get_Registration_Date(split_uhid):
    if len(split_uhid[0]) > 8:
        registration_date = datetime.strptime(split_uhid[-8:], '%y/%m/%d').strftime('%Y-%m%d')
    else:
        try:
            if split_uhid[1].count('*') == 1:
                split_uhid[1] = split_uhid[1].split('*')[0]

            registration_date = parser.parse(split_uhid[1].replace('*', '/')).strftime('%Y-%m-%d')

        except Exception as e:
            registration_date = ""
    return registration_date


def get_Date_From_Milliseconds(milliseconds):
    return datetime.fromtimestamp(milliseconds / 1000).strftime('%Y-%m-%d')


def generate_FHIR_Resource(data):
    patientData = data['after']

    patient_id = str(patientData['patient_id'])
    sex = patientData['sex']
    title = patientData['title']
    first_name = patientData['first_name']
    last_name = patientData['last_name']
    phone_number = patientData['phone_number']
    mobile_number = patientData['mobile_number']
    postal_code = patientData['postal_code']
    country = patientData['country']
    state = patientData['state']
    uhid_number = patientData['uhid_number']
    date_of_birth = patientData['date_of_birth']
    age = patientData['age']

    # FHIR variable
    phone = ""
    name = "Unknown"
    line = ""

    sex_map = {
        "MALE": "male",
        "FEMALE": "female",
        "TRANSGENDER": "other",
        "FE MALE": "female",
        "FEMLE": "female",
        "NONE": "unknown"
    }

    if (sex in ['', 'None', None, "NONE", "0"] and title in ["", 'None', None, "NONE", "DR", "Dr"]):
        sex = "unknown"
    elif sex in ['', 'None', None, "NONE", "0"] and title.upper() in ["MRS", "MISS", "MS", "MESSRS", "SELVI"]:
        sex = "female"
    elif sex in ['', 'None', None, "NONE", "0"] and title.upper() in ["MASTER", "MR"]:
        sex = "male"
    else:
        sex = sex_map.get(sex.upper(), "")

    if first_name and first_name.isalpha() and last_name and last_name.isalpha():
        name = f"{first_name} {last_name}"
    elif first_name and first_name.isalpha():
        name = first_name

    if phone_number not in ["None", None, "0000000000", "00000", "'", "PH NILL", "0", "00", "000", "000000000",
                            "000000"] and phone_number.isnumeric() and len(phone_number) == 10:
        phone = phone_number
    elif mobile_number not in ["None", None] and mobile_number.isnumeric():
        if len(mobile_number) == 10:
            phone = mobile_number
        elif len(mobile_number) > 10:
            mobile_number = mobile_number.replace(" ", "").replace("-", "").replace(",", "")
            if len(mobile_number) == 10:
                phone = mobile_number

    # if postal_code is none or 000000 or not equal to 6 digits, set it to ""
    if postal_code in ["", "None", "000000"] or len(postal_code) != 6:
        postal_code = ""

    country_map = {
        "INDIA": "India",
        "CHINA": "China",
        "KARUR": "India",
        "THIRUPPUR": "India",
        "INDI": "India",
        "TAMILNADU": "India",
        "COIMBATORE": "India",
        "AUSTRALIA": "Australia",
        "SENEGAL": "Senegal",
        "UNITED STATES": "United States of America",
        "ITALY": "Italy",
        "NIGERIA": "Nigeria",
        "FRANCE": "France",
        "SRI LANKA": "Sri Lanka",
        "KENYA": "Kenya",
        "INDONESIA": "Indonesia",
        "UGANDA": "Uganda",
        "SPAIN": "Spain",
        "PAKISTAN": "Pakistan",
        "KA": "India"
    }

    if country in ["", "None", "-"] or country.isnumeric():
        country = "India"
    else:
        # strip spaces and convert to upper case
        country = country_map.get(country.strip().upper(), "India")

    state_map = {
        "TAMILNADU": "Tamil Nadu",
        "KERALA": "Kerala",
        "KARNATAKA": "Karnataka"
    }

    if state in [None, "NONE", "None", "TAMIL NADU", "KERALA", "KARNATAKA"]:
        state = "Tamil Nadu"
    else:
        state = state_map.get(state.upper(), "Tamil Nadu")

    # for invalid and future dob and valid age
    if (date_of_birth in [None, "None", "", "0000-00-00 00:00:00", "null"] or
            get_Date_From_Milliseconds(date_of_birth)[:4] > datetime.now().strftime('%Y')):
        if age and age not in [None, "None", ""] and age.isdigit() and 0 < int(age) < 105:
            # calculate dob from uhid and age
            split_uhid = uhid_number.split('-')
            if len(split_uhid) >= 2:
                registration_date = get_Registration_Date(split_uhid)
                if registration_date:
                    try:
                        dob = datetime.strptime(registration_date, '%Y-%m-%d') - relativedelta(years=int(age))
                        date_of_birth = dob.strftime('%Y-%m-%d')
                    except Exception as e:
                        date_of_birth = ""
                else:
                    date_of_birth = ""
            else:
                date_of_birth = ""
        else:
            date_of_birth = ""
    else:
        date_of_birth = get_Date_From_Milliseconds(date_of_birth)

    patient = {"resourceType": "Patient", "id": str(uuid.uuid5(
        namespace=uuid.UUID('0a96ec42-0c26-11ed-b326-33f30ef759fd'), name=patient_id))}
    patient["name"] = [
        {
            "text": name
        }
    ]

    patient["identifier"] = [{
        "system": "https://ezovion.com/legacy_patient_id",
        "value": uhid_number
    }]

    patient["telecom"] = [
        {
            "system": "phone",
            "value": phone
        }
    ]

    patient["gender"] = sex

    if date_of_birth:
        patient['birthDate'] = date_of_birth

    address = {
        'use': "home",
        "state": state,
    }

    if line:
        address["line"] = [line]

    if postal_code:
        address["postalCode"] = postal_code

    patient["address"] = [address]

    return patient


if __name__ == "__main__":
    data = json.load(sys.stdin)

    if isinstance(data, list):
        output = [{"resource": generate_FHIR_Resource(patient), "request": {
            "method": "PUT",
            "url": "Patient/" + str(uuid.uuid5(namespace=uuid.UUID('0a96ec42-0c26-11ed-b326-33f30ef759fd'),
                                                  name=str(patient["after"]["patient_id"])))
        }} for patient in data]
    else:
        output = generate_FHIR_Resource(data)

    json.dump(output, sys.stdout)
