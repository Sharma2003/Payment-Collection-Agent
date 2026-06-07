from chat.Agent import Agent


def get_verified_agent():

    agent = Agent()

    agent.next("ACC1001")
    agent.next("Nithin Jain")
    agent.next("1990-05-14")

    return agent


def test_partial_payment():

    agent = get_verified_agent()

    response = agent.next("500")

    assert (
        "card"
        in response["message"].lower()
    )

    print("Partial Payment Passed")


def test_full_payment():

    agent = get_verified_agent()

    response = agent.next(
        "Pay full amount"
    )

    assert (
        "card"
        in response["message"].lower()
    )

    print("Full Payment Passed")


def test_invalid_amount():

    agent = get_verified_agent()

    response = agent.next("100000")

    assert (
        "balance"
        in response["message"].lower()
    )

    print("Invalid Amount Passed")


if __name__ == "__main__":

    test_partial_payment()
    test_full_payment()
    test_invalid_amount()