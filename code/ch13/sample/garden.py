"""garden.py: say which beds of the garden need water today.

  python3 garden.py [DAY]     DAY counts the days since the beds were
                              last watered together (default 0)
"""
import sys

# name of the bed -> (days between waterings, liters each time)
BEDS = {
    "tomatoes": (2, 6.0),
    "beans": (3, 4.0),
    "lettuce": (1, 2.5),
    "herbs": (4, 1.5),
}

def due(day):
    """Return the beds to water on the given day, in alphabetic order."""
    return sorted(bed for bed, (every, _) in BEDS.items()
                  if day % every == 0)

def liters(beds):
    """Return the water that the given beds need, in liters."""
    return sum(BEDS[bed][1] for bed in beds)

def report(day):
    beds = due(day)
    if not beds:
        return "day %d: nothing to water" % day
    return "day %d: water %s (%.1f liters)" % (
        day, ", ".join(beds), liters(beds))

if __name__ == "__main__":
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    for day in range(first, first + 7):
        print(report(day))
