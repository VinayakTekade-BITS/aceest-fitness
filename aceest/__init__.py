"""ACEest Fitness & Gym application package."""
from aceest import clients, membership, metrics, planner, programs, tracking

BLUEPRINTS = [programs.bp, clients.bp, tracking.bp, membership.bp, metrics.bp, planner.bp]
