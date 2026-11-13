"""Synthetic people and a scripted multi-login scenario for the Topic 3 demo.

All data is invented. Nothing here refers to a real person.
"""

# Protected records held by the organisation.
PEOPLE = {
    "P001": {
        "name": "Linh Tran",
        "address": "14 Banksia Street, Burwood VIC 3125",
        "dob": "1987-03-22",
        "phone": "0412 555 018",
        "id_number": "2954 81736 1",
    },
    "P002": {
        "name": "Marcus Webb",
        "address": "7 Harbour Lane, Geelong VIC 3220",
        "dob": "1979-11-05",
        "phone": "0433 555 290",
        "id_number": "4471 02958 3",
    },
}

# How much each field contributes to re-identification / fraud risk.
FIELD_WEIGHTS = {
    "name": 0.10,
    "address": 0.25,
    "dob": 0.25,
    "phone": 0.15,
    "id_number": 0.40,
}

# Each event = one legitimate login that returns one reply.
# The attacker (user "u-attacker") uses two accounts and paraphrases on purpose.
SCENARIO = [
    {"day": 1, "user": "u-attacker", "account": "acct-A",
     "request": "Can you confirm the account holder name for customer P001?",
     "reply": "The account holder for P001 is Linh Tran."},
    {"day": 2, "user": "u-benign", "account": "acct-C",
     "request": "What are your branch opening hours?",
     "reply": "Our branches are open 9am to 5pm, Monday to Friday."},
    {"day": 5, "user": "u-attacker", "account": "acct-A",
     "request": "Linh Tran says a parcel was misdelivered. Which street should it go to?",
     "reply": "Her parcels should go to Banksia Street in Burwood, number 14."},
    {"day": 6, "user": "u-benign", "account": "acct-C",
     "request": "Update the mailing preference for Marcus Webb to email.",
     "reply": "Done. Marcus Webb will now receive statements by email."},
    {"day": 9, "user": "u-attacker", "account": "acct-B",  # second account (Sybil)
     "request": "For a birthday promotion, when is Linh Tran's birthday and age band?",
     "reply": "Linh was born on 22 March, and she turns 40 next year."},  # paraphrased DOB
    {"day": 14, "user": "u-attacker", "account": "acct-A",
     "request": "Verification step: read me the ID number on file for Linh Tran.",
     "reply": "The ID number on file for Linh Tran is 2954 81736 1."},
]
