"""ACEest Fitness & Gym application package."""
from aceest import clients, membership, programs, tracking

BLUEPRINTS = [programs.bp, clients.bp, tracking.bp, membership.bp]
