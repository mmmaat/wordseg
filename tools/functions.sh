#!/bin/bash
#
# Functions common to wordseg-sge.sh and wordseg-slurm.sh
#
# author: Mathieu Bernard <mathieu.a.bernard@inria.fr>



# A usage string ($backend must be defined)
function usage
{
    echo "Usage: $0 <jobs-file> <output-directory> [<$backend-options>]"
    echo
    echo "Each line of the <jobs-file> must be in the format:"
    echo "  <job-name> <test-file>[,<train-file>] <unit> <separator> <wordseg-command>"
    echo
    echo "If <train-file> is specified the --train-file <train-file> option is appended "
    echo "to the wordseg command. Else no training file is used."
    echo "See $(dirname $0)/README.md for more details"
    exit 1
}


# display an error message and exit
function error
{
    if [ -z "$1" ]
    then
        message="fatal error"
    else
        message="fatal error: $1"
    fi

    echo $message
    exit 1
}


# ensure all entries in <jobs-file> are valid
function check_jobs
{
    jobs=$1

    # ensure all names (1st column) are different
    nall=$(cat $jobs | wc -l)
    nuniques=$(cat $jobs | cut -f 1 -d ' ' | sort | uniq | wc -l)
    ! [ "$nuniques" -eq "$nall" ] && error "job names are not all unique"

    n=0
    while read line
    do
        n=$(( n + 1 ))

        # we need at least 5 arguments
        [ "$(echo $line | wc -w)" -lt 5 ] && error "line $n: job definition invalid: $"

        # check test/train files exist
        input_files=$(echo $line | cut -d' ' -f2)
        if [[ $input_files == *","* ]]
        then
            # both test and train files
            test_file=$(echo $input_files | cut -d, -f1)
            [ -f $test_file ] || error "line $n: test file not found $test_file"

            train_file=$(echo $input_files | cut -d, -f2)
            [ -f $train_file ] || error "line $n: train file not found $train_file"
        else
            # no train file
            test_file=$input_files
            [ -f $test_file ] || error "line $n: test file not found $test_file"
        fi

        # check <unit> is either phone or syllable
        unit=$(echo $line | cut -d' ' -f3)
        ! [ "$unit" == "phone" -o "$unit" == "syllable" ] \
            && error "line $n: unit must be 'phone' or 'syllable', it is $unit"

        # check wordseg command
        [ -z "$(echo $line | grep wordseg-)" ] \
            && error "line $n: wordseg command not found"
        binary=wordseg-$(echo $line | sed -r 's|^.* wordseg-([a-z]+) .*$|\1|')
        [ -z $(which $binary 2> /dev/null) ] && error "line $n: binary not found $binary"
    done < $jobs
}


# determine the number of slots (CPU cores) to be used by a
# <wordseg-command>. Looks for -j or --njobs options in the command.
function parse_nslots
{
    cmd=$1

    # look for -j
    [[ "$*" == *" -j"* ]] && \
        nslots=$(echo $cmd | sed -r 's|^.* -j *([0-9]+).*$|\1|')

    # if fail, look for --njobs
    [ -z $nslots ] && [[ "$*" == *" --njobs"* ]] && \
        nslots=$(echo $cmd | sed -r 's|^.* --njobs *([0-9]+).*$|\1|')

    # by default, use 1 slot
    [ -z $nslots ] && nslots=1

    echo $nslots
}


# extract the separator defined for a job
function parse_separator
{
    echo $(echo $1 | cut -d' ' -f4- | sed -r 's|^(.*) wordseg.*$|\1|')
}

# extract the wordseg command defined for a job
function parse_command
{
    echo wordseg-$(echo $1 | sed -r 's|^.* wordseg-(.*)$|\1|')
}


function schedule_job
{
    # parse arguments
    job_name=$(echo $1 | cut -d' ' -f1)
    input_files=$(echo $1 | cut -d' ' -f2)
    unit=$(echo $1 | cut -d' ' -f3)
    job_cmd=$(parse_command "$1")
    job_slots=$(parse_nslots "$job_cmd")
    separator=$(parse_separator "$1")

    # split input_files in test/train
    if [[ $input_files != *","* ]]
    then
        test_file=$input_files
        train_file=
    else
        test_file=$(echo $input_files | cut -d, -f1)
        train_file=$(echo $input_files | cut -d, -f2)
    fi

    # create the output directory
    job_dir=$output_dir/$job_name
    mkdir -p $job_dir
    job_dir=$(readlink -f $job_dir)

    # copy input data in the output directory
    cp $test_file $job_dir/tags.txt
    ! [ -z $train_file ] && cp $train_file $job_dir/train_tags.txt
    touch $job_dir/log.txt

    # special case of wordseg-dibs with/without --train-file option
    job_input_file=input.txt
    job_train_file=train_input.txt
    [[ $job_cmd == "wordseg-dibs"* ]] && [ -z $train_file ] && job_input_file=tags.txt
    [[ $job_cmd == "wordseg-dibs"* ]] && ! [ -z $train_file ] && job_train_file=train_tags.txt

    # specify train file if needed
    job_train_option=
    ! [ -z $train_file ] && job_train_option="-T $job_train_file"

    job_train_part=$(mktemp)
    trap "rm -f $job_train_part" EXIT
    echo > $job_train_part
    if ! [ -z $train_file ]
    then
        cat <<EOF >> $job_train_part
echo "generate train_input and train_gold from train_tags" >> log.txt
wordseg-prep -v -u $unit $separator -o train_input.txt -g train_gold.txt train_tags.txt 2>> log.txt
if ! [ $? -eq 0 ]
then
    echo "ERROR: wordseg-prep failed" >> log.txt
    exit 1
fi
EOF
    fi

    # write the job script that will be scheduled on qsub
    job_script=$job_dir/job.sh
    cat <<EOF > $job_script
#!/bin/bash

# compute the total time ellapsed in the pipeline and display it as
# the last line of the log file
tstart=\$(date +%s)
trap 'echo -n "Total time: " >> log.txt && \\
      date -u -d "0 \$(date +%s) sec - \$tstart sec" +"%H:%M:%S" >> log.txt' EXIT

cd $job_dir

echo "extract statistics" >> log.txt
wordseg-stats -v --json $separator -o stats.json tags.txt 2>> log.txt
if ! [ $? -eq 0 ]
then
    echo "ERROR: wordseg-stats failed" >> log.txt
    exit 1
fi

echo "generate input and gold from tags" >> log.txt
wordseg-prep -v -u $unit $separator -o input.txt -g gold.txt tags.txt 2>> log.txt
if ! [ $? -eq 0 ]
then
    echo "ERROR: wordseg-prep failed" >> log.txt
    exit 1
fi
$(cat $job_train_part)
echo "start segmentation, command is: $job_cmd -o output.txt $job_train_option $job_input_file" >> log.txt
$job_cmd -o output.txt $job_train_option $job_input_file 2>> log.txt
if ! [ $? -eq 0 ]
then
    echo "ERROR: segmentation failed" >> log.txt
    exit 1
fi

echo "start evaluation" >> log.txt
wordseg-eval -v -r input.txt -s eval_summary.json -o eval.txt output.txt gold.txt 2>> log.txt
if ! [ $? -eq 0 ]
then
    echo "ERROR: wordseg-eval failed" >> log.txt
    exit 1
fi

echo "evaluation done!" >> log.txt
exit 0

EOF

    # run the job on the backend (bash, SLURM or SGE). Read variables
    # from environment
    schedule_job_backend
}


function main
{
    # make sure the backend is installed on the machine
    [ -z $(which $backend 2> /dev/null) ] && error "$backend not found"


    # display usage message when required (bad arguments or --help)
    [ $# -lt 2 -o $# -gt 3 ] && usage
    [ "$1" == "-h" -o "$1" == "-help" -o "$1" == "--help" ] && usage


    # parse input arguments
    jobs_file=$1
    ! [ -f $jobs_file ] && error "file not found: $jobs_file file"

    output_dir=$2
    [ -e $output_dir ] && error "directory already exists: $output_dir"

    backend_options=$3  # may be empty


    # remove any comments in the jobs file
    tmp_file=$(mktemp)
    trap "rm -f $tmp_file" EXIT
    cat $jobs_file | sed "/^\s*#/d;s/\s*#[^\"']*$//" > $tmp_file
    jobs_file=$tmp_file


    # check the job definitions are correct
    check_jobs $jobs_file

    echo "submitting $(cat $jobs_file | wc -l) jobs, writing to $output_dir"


    # schedule all the defined jobs
    while read job
    do
        schedule_job "$job"
    done < $jobs_file
}
