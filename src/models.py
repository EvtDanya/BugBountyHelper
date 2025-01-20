from dataclasses import dataclass


@dataclass
class BugBountyProgram(object):
    program_type: str = "Bug Bounty"
    name: str = None
    company: str = None
    description: str = None
    reward: str = None
    url: str = None

    def __init__(
        self,
        name: str,
        company: str,
        description: str,
        reward: str,
        url: str
    ):
        """
        Initialize an object
        """
        self.name = name
        self.company = company
        self.description = description
        self.reward = reward
        self.url = url

        self._check_type()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def _check_type(self):
        if self.company == "Кибериспытание":
            self.company = self.name
            self.program_type = "Кибериспытание"

