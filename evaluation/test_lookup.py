from chat.Agent import Agent


def test_valid_account():

    agent = Agent()

    response = agent.next("ACC1001")

    assert (
        "full name"
        in response["message"].lower()
    )

    print("Valid Account Lookup Passed")


def test_invalid_account():

    agent = Agent()

    response = agent.next("ACC9999")

    assert (
        "couldn't find"
        in response["message"].lower()
        or
        "not found"
        in response["message"].lower()
    )

    print("Invalid Account Lookup Passed")


if __name__ == "__main__":

    test_valid_account()
    test_invalid_account()