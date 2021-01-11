# PDF Parsing for TRS rates

Assumes PDF format of https://www.twc.texas.gov/files/policy_letters/attachments/wd-25-20-att.1-wfed.pdf and uses AWS Textract.

## Running

1. Setup AWS credentials/config with Textract enabled
2. Install Python 3.9
3. `pipenv install`
4. `pipenv run python main.py <path_to_pdf>`