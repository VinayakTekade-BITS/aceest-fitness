"""ACEest Fitness & Gym application package."""
from aceest import clients, membership, metrics, programs, tracking

BLUEPRINTS = [programs.bp, clients.bp, tracking.bp, membership.bp, metrics.bp]
