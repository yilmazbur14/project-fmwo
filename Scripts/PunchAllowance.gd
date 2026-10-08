extends RefCounted

# What one opening lets the player's punches take off a boss: the damage a clean chain of its cap's
# punches deals (clean_chain), wherever in the combo the punches fall. The combo has no timing and
# carries its count from one opening into the next (PlayerCombo), so an opening can start anywhere in
# it: on its POW, or with a POW due that is cut down to what is left. Spent in damage, nothing can take
# more than the chain would. It replaced a cap on landed punches, which a combo broken before its POW
# spent back when the combo had timing: the charged punch was refused, and every punch after it too,
# silently, for the rest of an opening that still looked wide open. The combo's own numbers
# (PlayerCombo.hits_to_charge and charged_damage) are these.
# A boss keeps one (`var punches := PunchAllowance.new()`) and asks it in take_punch(), handing it his
# own count of punches landed this opening. His window states zero that count as each opening starts,
# which is how it knows a new one has begun.

const HITS_TO_CHARGE := 3
const CHARGED_DAMAGE := 2

var spent := 0


# The damage a clean chain of `hits` punches deals: every HITS_TO_CHARGE-th one is the charged one.
static func clean_chain(hits: int) -> int:
	var total := 0
	for i in hits:
		total += CHARGED_DAMAGE if i % HITS_TO_CHARGE == HITS_TO_CHARGE - 1 else 1
	return total


# How much of a punch worth `amount` still lands in an opening worth a clean `cap_hits`-punch chain:
# all of it, what is left, or 0. `landed` is the boss's count of punches landed this opening.
func allow(amount: int, landed: int, cap_hits: int) -> int:
	if landed == 0:
		spent = 0
	return clampi(clean_chain(cap_hits) - spent, 0, amount)


func spend(dealt: int) -> void:
	spent += dealt
