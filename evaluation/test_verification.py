from chat.Agent import Agent


def test_verification_with_dob():

    agent = Agent()

    agent.next("ACC1001")
    agent.next("Nithin Jain")

    response = agent.next("1990-05-14")

    assert (
        "verified"
        in response["message"].lower()
    )

    print("Verification using DOB Passed")


def test_verification_with_aadhaar():

    agent = Agent()

    agent.next("ACC1001")
    agent.next("Nithin Jain")

    response = agent.next("4321")

    assert (
        "verified"
        in response["message"].lower()
    )

    print("Verification using Aadhaar Passed")


def test_verification_with_pincode():

    agent = Agent()

    agent.next("ACC1001")
    agent.next("Nithin Jain")

    response = agent.next("400001")

    assert (
        "verified"
        in response["message"].lower()
    )

    print("Verification using Pincode Passed")


def test_wrong_name():

    agent = Agent()

    agent.next("ACC1001")
    agent.next("Wrong Name")

    response = agent.next("1990-05-14")

    assert (
        "failed"
        in response["message"].lower()
    )

    print("Wrong Name Verification Test Passed")


def run():
    test_verification_with_dob()
    test_verification_with_aadhaar()
    test_verification_with_pincode()
    test_wrong_name()