#!/usr/bin/env bash
####
################################## START OF EMBEDDED SGE COMMANDS ##########################
######## Common options ########
#$ -S /bin/bash  #### Default Shell to be Used
#$ -cwd  #### Run in current directory
#$ -N rGreedy_Deformable  #### Job Name to be listed in qstat
#$ -j y #### merge stdout and stderr to a single file at -o path
#$ -l h_vmem=32G #### How much memory total the job can use. Defaults to 4GB ( qconf -sc | grep h_vmem ) - My experience has been: Minimum 50
#$ -l tmpfree=8G #### How much scratch space the job can use. Defaults to 0GB if not specified by user
############################## END OF DEFAULT EMBEDDED SGE COMMANDS #######################

#user input as getopts
input=;
segm=;
mask=;
atlas=;
outdir=;
atlas_segm=;

output=;
output_affine=;
output_affine_mat=;
output_deform=;

iteration="100x50x10"
metric="NCC 2x2x2"
interpolation="LINEAR"

#Flags
applydeform=0;
applydeform_inverse=0;

echoV()
{
    #echo only IF VERBOSE flag is on
    if [ ${VERBOSE} -eq 1 ];
    then
        echo -e $1;
    fi;
}

exit_if_blank()
{
    argument_value="$1";
    argument_name="$2";
    if [ -z "${argument_value}" ];
    then
        echo -e "\nparameter argument (${argument_name}) was not provided. Exiting.";
        exit 1;
    fi;
}

exit_if_not_exist()
{
    file="$1";
    if [ ! -e "${file}" ]; then
        echo -e "\nfile (${file}) does not exist. Exiting.";
        exit 1;
    fi;
}
exit_if_not_exist_dir()
{
    file="$1";
    if [ ! -d "${file}" ]; then
        echo -e "\nfolder (${file}) does not exist. Exiting.";
        exit 1;
    fi;
}

exit_if_exist()
{
    file="$1";
    if [ -e "${file}" ]; then
        echo -e "\nfile (${file}) already exists. Exiting.";
        exit 1;
    fi;
}

check_extension()
{
    #check for extension of the input file (first argument)
    #option to check versus just one extension (filename.extension1) or two extensions (filename.extension1.extension2)
    file="$1";
    extension1="$2";
    extension2="$3";

    echoV "\n";
    echoV "---> check_extension";
    echoV "---> file: (${file})";
    echoV "---> extension1: (${extension1})";
    if [ ! -z "${extension2}" ];
    then
        echoV "---> extension2: (${extension2})";
    fi;

    file_basename=$(basename "${file}");
    file_directory=$(dirname "${file}");
    file_extension1="${file_basename##*.}";
    file_no_extension1="${file_basename%.*}";
    file_extension2="${file_no_extension1##*.}";
    file_no_extension2="${file_no_extension1%.*}";

    echoV "---> file_basename: (${file_basename})";
    echoV "---> file_directory: (${file_directory})";
    echoV "---> file_extension1: (${file_extension1})";
    echoV "---> file_no_extension1: (${file_no_extension1})";
    echoV "---> file_extension2: (${file_extension2})";
    echoV "---> file_no_extension2: (${file_no_extension2})";
    echoV "\n";

    if [ "${file_extension1}" != "${extension1}" ];
    then
        echo -e "\nfile (${file}) is not of type ${extension1}, but has extension ${file_extension1}. Exiting.";
        exit 1;
    fi;

    if [ ! -z "${extension2}" ];
    then
        if [ "${file_extension1}" == "${extension1}" ] && [ "${file_extension2}" != "${extension2}" ];
        then
            echo -e "\nfile (${file}) is not of type ${extension2}.${extension1}, but has extension ${file_extension2}.${file_extension1}. Exiting.";
            exit 1;
        fi;
    fi;
}


function Help {

  echo -e "${REGULAR_RED}";

  echo -e "\n";
  echo -e "  Description:";

  echo -e "\n";
  echo -e "    Using Greedy, performs deformable registration of input image to reference image."
  echo -e "    There are two main usages for this script:";
  echo -e "      1. Obtain the affine and deformable transformation, and (optionally) apply to input image to move to the reference space.";
  echo -e "      2. Apply user provided affine and deformable transformation to move input image to reference space.";

  echo -e "    Please refer to Greedy documentation for more details, options, and citation"
  echo -e "    https://sites.google.com/view/greedyreg/about"
  echo -e "    Description Verbose.";

  echo -e "\n";
  echo -e "  Usage:";

  echo -e "\n";
  echo -e "    ${script_name}  -o /output/directory -i /path/to/image.nii.gz -a /path/to/atlas.nii.gz  [-OPTION argument]"

  echo -e "\n";
  echo -e "  Compulsory Arguments:";

  echo -e "\n";
  echo -e "    -i	 [path]/full/path/to/${UNDERLINE_YELLOW}i${REGULAR_RED}nput/file";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}input${REGULAR_RED})";
  echo -e "    (must be nii.gz)";

  echo -e "\n";
  echo -e "    -r	 [path]/full/path/to/${UNDERLINE_YELLOW}r${REGULAR_RED}eference/file/to/register/to";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}atlas${REGULAR_RED})";
  echo -e "    (must be nii.gz)";
    
  echo -e "\n";
  echo -e "    -m	 [path]/full/path/to/${UNDERLINE_YELLOW}m${REGULAR_RED}atrix/of/affine/transformation";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}matrix${REGULAR_RED})";
  echo -e "    (must be .mat)";
  echo -e "    (1. Default usage: Use Greedy to calculate/output matrix";
  echo -e "     2. -a option: Apply the input affine transformation and output image)";

  echo -e "\n";
  echo -e "    -d	 [path]/full/path/to/${UNDERLINE_YELLOW}d${REGULAR_RED}eformation/field/file"
  echo -e "    (variable name: ${UNDERLINE_YELLOW}matrix${REGULAR_RED})";
  echo -e "    (must be .nii.gz)";
  echo -e "    (1. Default usage: Use Greedy to calculate/output deformation";
  echo -e "     2. -a option: Apply the input deformation and output image )";


  echo -e "\n";
  echo -e "  Optional Arguments:";

  echo -e "\n";
  echo -e "    -o	 [path]/full/path/to/${UNDERLINE_YELLOW}o${REGULAR_RED}utput/deformably/registered/image";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}output${REGULAR_RED})";
  echo -e "    (must be nii.gz)";

  echo -e "\n";
  echo -e "    -a	 [switch]";
  echo -e "    (Applies provided transformation to input image and output registered image. No optimisation.)";

  echo -e "\n";
  echo -e "    -b	 [switch]";
  echo -e "    (Applies inverse deformation. Must be used together with -a )";
  echo -e "    (usage: -a -b -m mov_to_fix.mat,-1 -d mov_to_fix_deform_inv.nii.gz)";

  echo -e "\n";
  echo -e "    -k	 [path]/full/path/to/${UNDERLINE_YELLOW}m${REGULAR_RED}ask/file/for/skull/stripping/that/helps/with/registration";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}mask${REGULAR_RED})";
  echo -e "    (must be nii.gz)";

  echo -e "\n";
  echo -e "    -u	 [path]/full/path/to/${UNDERLINE_YELLOW}o${REGULAR_RED}utput/affine/registered/image";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}output_affine${REGULAR_RED})";
  echo -e "    (must be nii.gz)";

  echo -e "\n";
  echo -e "    -e	 [string]m${UNDERLINE_YELLOW}e${REGULAR_RED}tric for affine registration";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}metric${REGULAR_RED})";
  echo -e "    (default=${metric})";
  echo -e "    (must be string among the following options:";
  echo -e "      SSD:          sum of square differences (default)";
  echo -e "      MI:           mutual information";
  echo -e "      NMI:          normalized mutual information";
  echo -e "      NCC <radius>: normalized cross-correlation";
  echo -e "      MAHAL:        Mahalanobis distance to target warp";
  echo -e "    )";
  echo -e "    (these options are based on the current greedy usage. They are subject to change by the writer/maintainer of greedy.)";
  echo -e "    (This option will be ignored when using -a option)"

  echo -e "\n";
  echo -e "    -p	 [string]inter${UNDERLINE_YELLOW}p${REGULAR_RED}olation method.";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}interpolation${REGULAR_RED})";
  echo -e "    (default=${interpolation})";
  echo -e "    (must be string among the following:";
  echo -e "      NN:          nearest neighbor";
  echo -e "      LINEAR:      linear interpolation";
  echo -e "      LABEL sigma: for label interpolation, where sigma is amount of smoothing. Quoting the greedy documentation online:";
  echo -e "                   This mode applies a little bit of smoothing to each label in your segmentation (including the background),"
  echo -e "                   warps this smoothed segmentation, and then performs voting among warped smoothed binary segmentations to "
  echo -e "                   assign each voxel in reference space a label. This works better than nearest neighbor interpolation (less aliasing)."
  echo -e "                   Sigma value, such as 0.2vox, part of the command specifies the amount of smoothing.";

  echo -e "\n";
  echo -e "    -t	 [\"int\"x\"int\"x\"int\"]i${UNDERLINE_YELLOW}t${REGULAR_RED}erations of optimization at each level.";
  echo -e "    (variable name: ${UNDERLINE_YELLOW}iteration${REGULAR_RED})";
  echo -e "    (default=${iteration})";
  echo -e "    (must be three positive integers concatenated with \"x\" alphabet in between without any spacing)";
  echo -e "    (e.g. 100x50x10 says to do 100 iterations of optimization at lowest resolution level, 50 at intermediate resolution and 10 at full resolution.)";

  echo -e "\n";
  echo -e "    -V  [switch]${UNDERLINE_YELLOW}V${REGULAR_RED}ERBOSE mode on";
  echo -e "    (default=${VERBOSE})";

  echo -e "${RESET_ALL}";
};

#get user inputs
while getopts hi:o:m:d:u:r:k:e:p:t:Vab option
do
  case "${option}"
  in
    h)	Help;    #show help documentation
        exit 0;
        ;;
    i)  input=${OPTARG};;   #nii.gz
    o)	output=${OPTARG};;  #nii.gz
    a)  applydeform=1;;
    b)  applydeform_inverse=1;;
    m)	output_affine_mat=${OPTARG};;  #mat
    d)	output_deform_field=${OPTARG};;  #nii.gz
    u)  output_affine=${OPTARG};; #nii.gz #optional
    r)	atlas=${OPTARG};;   #nii.gz
    k)	mask=${OPTARG};;     #nii.gz
    e)  metric=${OPTARG};; #string
    p)  interpolation=${OPTARG};; #string
    t)  iteration=${OPTARG};; #string 
    V)	VERBOSE=1;
        echoV "VERBOSE Mode on";
        ;;
    ?)	echo "Unrecognized Options. Exiting. " 1>&2;
        Help;
        exit 1;
        ;;
  esac
done;


#sanity check 1: did user input mandatory arguments?
echoV "\n---> Checking if required input arguments were given";
exit_if_blank "$input" "input";
exit_if_blank "$output" "output";
exit_if_blank "$atlas" "atlas";
exit_if_blank "$output_affine_mat" "output_affine_mat";
exit_if_blank "$output_deform_field" "output_deform_field";

echoV "\n---> Checking if path to files have correct, expected extensions.";
check_extension "$input" "gz" "nii";
check_extension "$output" "gz" "nii";
check_extension "$atlas" "gz" "nii";
check_extension "$output_deform_field" "gz" "nii";
#check_extension "$output_affine_mat" "mat";  ## removing so you can do ,-1
for f in $output_affine_mat; do
    if [[ "$f" == *",-1" ]]; then fcheck=${f%,-1}; else fcheck=$f; fi #added to remove -1 for applying inverse
    check_extension $fcheck "mat";
done

#sanity check 2: if output already exists, quit before proceeding further
echoV "\n---> Checking if output file already exists";
exit_if_exist "$output";

#sanity check 2.1: if output is file path (not directory), then check if output directory exists
echoV "\n---> Checking if output directory does not exist";
if (( $applydeform == 1 )); then
    outdir=`dirname $output`
else
    outdir=`dirname $output_affine_mat`
fi
exit_if_not_exist_dir "$outdir";

#sanity check 3: does input exist?
echoV "\n---> Checking if input file exists";
exit_if_not_exist "$input";
exit_if_not_exist "$atlas";
if [ $applydeform == 1 ]; then
    # exit_if_blank "$output" "output";
    # check_extension "$output" "gz" "nii";
    exit_if_not_exist "$output_deform_field";
    if [ ! -z $mask ]; then
	echo "Apply Deformation (no optimization) mode selected. Input mask will be ignored."
    fi
    #exit_if_not_exist "$output_affine_mat";
    for f in $output_affine_mat; do
        if [[ "$f" == *",-1" ]]; then fcheck=${f%,-1}; else fcheck=$f; fi #added to remove -1 for applying inverse
        exit_if_not_exist "$fcheck";
    done
    
else
    if [ ! -z $mask ]; then
	exit_if_not_exist "$mask";
	check_extension "${mask}" "gz" "nii";
    fi
fi

#sanity check 4: do executables exist?
echoV "\n---> Checking module and executable availability";

greedy_executable=`which greedy`
exit_if_not_exist "${greedy_executable}";


#output to log file relevant arguments
echo -e "input:\t(${input})";
echo -e "atlas:\t(${atlas})";
echo -e "outdir:\t(${outdir})";
echo -e "output:\t(${output})";
echo -e "output_affine_mat:\t(${output_affine_mat})";
echo -e "output_deform_field:\t(${output_deform_field})";
echo -e "greedy_executable:\t(${greedy_executable})";
echo -e "apply existing (no optimization):\t($applydeform)"
echo -e "apply existing inverse (deform then affine):\t($applydeform_inverse)"


if [ ! -z $mask ];
then
  echo -e "mask:\t(${mask})";
fi;

echo -e ""
echo -e "############### start processing ################"
echo -e ""

#processing 1: copy files to tmpdir

tmpdir=$outdir/tmp
mkdir -pv $tmpdir

echo -e "\n---> copying input files to tmpdir ($tmpdir)"; #in order to not expose path to user when using ipp

cmd="cp -L $input $tmpdir/input.nii.gz"
echo -e "\n> $cmd"
$cmd

cmd="cp -L $atlas $tmpdir/atlas.nii.gz"
echo -e "\n> $cmd"
$cmd

if [ $applydeform == 0 ]; then
    if [ ! -z $mask ]; then
	cmd="cp -L $mask $tmpdir/mask.nii.gz"
	echo -e "\n> $cmd"
	$cmd
    fi
fi


#### step1. affine registration  
# Skip step1 and step2 if applying tranformation only

if [ $applydeform == 0 ]; then

    echo -e "\n---> Performing Greedy Affine Registration to acquire the transformation matrix ($tmpdir/affine.mat)"
    ### maskoption - to be used for both affine and deformable registration
    if [ ! -z $mask ]; then
	maskoption="-gm $tmpdir/mask.nii.gz"
    else
	maskoption=;
    fi

    ### other greedy options

    greedy_option="-m $metric -n $iteration";

    ###

    if [ ! -f $output_affine_mat ]; then

	cmd="${greedy_executable} \
      	     -d 3 -a -threads 1 \
	     $greedy_option \
	     -i $tmpdir/atlas.nii.gz $tmpdir/input.nii.gz \
	     -ia-image-centers \
	     -o $tmpdir/affine.mat \
	     $maskoption"
	echo -e "\n> $cmd"
	$cmd

	if [ ! -f $tmpdir/affine.mat ]; then
	    echo -e "\nAffine registration failed. Exiting"
	    exit 1;
	else
	    cmd="cp -L $tmpdir/affine.mat $output_affine_mat"
	    echo -e "\n> $cmd"
	    $cmd
	fi
    else
	echo -e "$output_affine_mat already exists. Copying to tmpdir."
	cmd="cp -L $output_affine_mat $tmpdir/affine.mat"
	echo -e "\n> $cmd"
	$cmd
    fi;

    ### step2 deformable registration


    echo -e "\n---> Performing Greedy Deformable Registration to obtain Deformation field file ($tmpdir/deform.nii.gz)"

    if [ ! -f $output_deform_field ]; then

	cmd="${greedy_executable} \
	     -d 3 -threads 1 \
	     $greedy_option \
	     -i $tmpdir/atlas.nii.gz $tmpdir/input.nii.gz \
	     -it $tmpdir/affine.mat \
	     -o $tmpdir/deform.nii.gz \
	     -oinv $tmpdir/deform_inv.nii.gz \
	     $maskoption"
	echo -e "\n> $cmd"
	$cmd
	
	## save inverse deformation field too. use name of deformation field
	tmp=`basename $output_deform_field`;
	tmpd=`dirname $output_deform_field`;
	tmp=${tmp%.nii.gz}
	output_deform_field_inv="$tmpd/${tmp}_inv.nii.gz"
	
	if [ ! -f $tmpdir/deform.nii.gz ]; then
	    echo "Deformable registration failed. Exiting"
	    exit 1;
	else
	    cmd="cp -L $tmpdir/deform.nii.gz $output_deform_field"
	    echo -e "\n> $cmd"
	    $cmd
	    cmd="cp -L $tmpdir/deform_inv.nii.gz $output_deform_field_inv"
	    echo -e "\n> $cmd"
	    $cmd
	fi
    else
	echo -e "$output_deform_field already exists. Copying to tmpdir."
	cmd="cp -L $output_deform_field $tmpdir/deform.nii.gz"
	echo -e "\n> $cmd"
	$cmd
    fi;
    
fi

#############################################################

## warping to atlas


# optional- output affine registration of input image

if [ ! -z $output_affine ]; then

    echo -e "\n---> Moving input image to reference, using affine matrix only...\n"
    
    if [ ! -f $output_affine ]; then
	cmd="${greedy_executable} \
	-d 3 -threads 1 \
	-rf $tmpdir/atlas.nii.gz \
	-ri ${interpolation} \
	-rm $tmpdir/input.nii.gz $tmpdir/output_affine.nii.gz \
	-r $tmpdir/affine.mat"
	echo -e "\n> $cmd"
	$cmd
	
	if [ ! -f $tmpdir/output_affine.nii.gz ]; then
	    echo "Moving image (affine) failed. Exiting."
	    exit 1;
	else
	    cmd="cp -L $tmpdir/output_affine.nii.gz $output_affine"
	    echo -e "\n> $cmd"
	    $cmd
	fi
    else
	echo -e "$output_affine already exists. Skipping."
    fi;
fi   


# Using both affine and deformable

echo -e "\n---> Moving input image to reference, using deformation field and affine matrix ...\n"

if [ ! -f $output ];
then

    if (( applydeform==0 ));
    then
	transform="$tmpdir/deform.nii.gz $tmpdir/affine.mat"
    else
	if (( applydeform_inverse==0 )); then
	    transform="$output_deform_field $output_affine_mat"
	else	 
	    transform="$output_affine_mat $output_deform_field"
	fi
    fi

    cmd="${greedy_executable} \
           -d 3 -threads 1 \
	   -rf $tmpdir/atlas.nii.gz \
	   -ri ${interpolation} \
	   -rm $tmpdir/input.nii.gz $tmpdir/output.nii.gz \
	   -r $transform"
    echo -e "\n> $cmd"
    $cmd

    if [ ! -f $tmpdir/output.nii.gz ]; then
	echo "Moving image (deformable) failed. Exiting."
	exit 1;
    else
	cmd="cp -L $tmpdir/output.nii.gz $output"
	echo -e "\n> $cmd"
	$cmd
    fi
fi

echo -e "\nfinished."
