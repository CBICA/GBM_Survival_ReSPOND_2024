#!/bin/sh
# script for execution of deployed applications
#
# Sets up the MATLAB Runtime environment for the current $ARCH and executes 
# the specified command.
#
exe_name=$1
exe_dir=`dirname $exe_name`
echo "------------------------------------------"

if [[ "$1" == "" ]]; then
    echo "Usage: run_matlabexec_2018a.sh matlabexec [arguments]"
    exit;	 
else

    echo Setting up environment variables

    ### edit path to your local path:

    MCRROOT="/your/path/to/matlab/dir/matlab/R2018A"

    ####

    
    if [ ! -d $MCRROOT ]; then
	echo "Error: Matlab root directory not found."
	echo "Please edit the path inside the run_matlabexec_2018a.sh script to specify your local path and retry."
        exit
    fi
       

    LD_LIBRARY_PATH=.:${MCRROOT}/runtime/glnxa64 ;
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/bin/glnxa64 ;
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/os/glnxa64;
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${MCRROOT}/sys/opengl/lib/glnxa64;
    export LD_LIBRARY_PATH;
    echo "LD_LIBRARY_PATH is: ${LD_LIBRARY_PATH}";

    shift 1
    args=;
    while [ $# -gt 0 ]; do
	token=$1
	args="${args} \"${token}\"" 
	shift
    done
    echo "$exe_name $args"
    eval "$exe_name $args"
fi

exit

