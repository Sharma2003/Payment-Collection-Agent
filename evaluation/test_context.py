from chat.Agent import Agent


def test_context_persistence():

    agent = Agent()

    agent.next("ACC1001")

    response = agent.next("Nithin Jain")

    assert (
        "date of birth"
        in response["message"].lower()
        or
        "aadhaar"
        in response["message"].lower()
    )

    response = agent.next("1990-05-14")

    assert (
        "verified"
        in response["message"].lower()
    )

    print("Context Persistence Passed")


def test_out_of_order_input():

    agent = Agent()

    agent.next("My name is Nithin Jain")

    agent.next("ACC1001")

    response = agent.next("1990-05-14")

    assert (
        "verified"
        in response["message"].lower()
    )

    print("Out Of Order Input Passed")


if __name__ == "__main__":

    test_context_persistence()
    test_out_of_order_input()