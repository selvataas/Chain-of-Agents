if __name__ == "__main__":
    from chain_of_agents.main import ChainOfAgents

    text = "Your long input text goes here. It should be long enough to be split into chunks..."
    query = "Summarize the content."

    chain = ChainOfAgents()
    result = chain.process(text, query)

    print("\n💬 Final Output:")
    print(result)
