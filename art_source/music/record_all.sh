#!/usr/bin/env bash
# Records every approved *_theme_v3.rb, cuts one seamless cycle out of each, and reports the level
# of both the take and the cut. One theme at a time - they all want the same sound card.
#
#   RAW=/somewhere bash art_source/music/record_all.sh [name ...]
#
# With no names it does all eight. RAW defaults to a raw/ beside this script; point it at a scratch
# directory, because the takes are ~40 MB each and none of them belong in a public repo.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/../.." && pwd)"
RAW="${RAW:-$HERE/raw}"
CUT="${CUT:-$HERE/cut}"
mkdir -p "$RAW" "$CUT"

# Every theme's tempo, taken from its own use_bpm. Danny's take needs a later offset: his piece opens
# on a pickup, so the first transient is not the downbeat.
declare -A BPM=( [eric]=138 [greyson]=160 [carter]=150 [mason]=165 [josh]=168 [liam]=144 [jordan]=180 [danny]=160 )
declare -A EXTRA=( [danny]="--offset 1.5" )

NAMES=("$@")
if [ "${#NAMES[@]}" -eq 0 ]; then
	NAMES=(eric greyson carter mason josh liam jordan danny)
fi

fails=0
for name in "${NAMES[@]}"; do
	bpm="${BPM[$name]:-}"
	if [ -z "$bpm" ]; then
		echo "!! no tempo known for $name"
		fails=$((fails + 1))
		continue
	fi
	src="$HERE/${name}_theme_v3.rb"
	take="$RAW/${name}_theme_v3_raw.wav"
	out="$CUT/${name}_theme.wav"
	echo "=================== $name ($bpm bpm) ==================="
	if ! python "$HERE/record_theme.py" "$src" "$bpm" --out "$take"; then
		echo "!! $name: the take failed"
		fails=$((fails + 1))
		continue
	fi
	python "$HERE/measure_take.py" "$take" "$bpm"
	if ! python "$HERE/cut_loop.py" "$take" "$bpm" ${EXTRA[$name]:-} --out "$out"; then
		echo "!! $name: the cut failed"
		fails=$((fails + 1))
		continue
	fi
	python "$HERE/measure_take.py" "$out" "$bpm"
	echo
done
echo "== themes that failed: $fails"
exit $((fails > 0))
