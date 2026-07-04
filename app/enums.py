import enum


class UserRole(enum.Enum):
    REVIEWER = 'reviewer'
    ADMIN = 'admin'


class CandidateStatus(enum.Enum):
    NEW = 'new'
    REVIEWED = 'reviewed'
    HIRED = 'hired'
    REJECTED = 'rejected'
    ARCHIVED = 'archived'
