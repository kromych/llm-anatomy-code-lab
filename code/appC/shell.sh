# shell.sh -- the constructs that the shell listings of this book rely on.
# The lines ran one by one under zsh and under bash on macOS:
#     zsh -v shell.sh        (-v prints each line before running it)
# They create a directory demo where they run and remove it at the end.
mkdir demo && cd demo                 # && goes on if mkdir succeeded
port=8097                             # a variable; no spaces around =
echo "port $port" > a.txt; echo 'port $port' > b.txt
cat *.txt                             # * stands for any file name
echo "user $(id -u) wrote $(cat *.txt | grep -c port) lines;" \
     "HF_HOME is ${HF_HOME:-not set}"
ls c.txt && echo "found c.txt"        # ls fails, so echo does not run
for f in a b; do wc -c $f.txt; done
cd .. && rm -r demo
