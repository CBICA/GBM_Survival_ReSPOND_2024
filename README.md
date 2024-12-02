# GBM_Survival_ReSPOND_2024

This repository includes the source codes to evaluate the survival model described in our paper
"Machine Learning-based Prognostic Subgrouping of Glioblastoma: A Multi-center Study"
Neuro-Oncology 2024


### Code description

- src/FeatEx.m : function to extract features

- src/GBMSurvival_predict.m : matlab fuction to run predictions

- src/run_GBMsurvival_predict.sh: Bash wrapper to extract features from images, apply the pretrained model, and output a report.
Inputs are patient age, preprocessed MRI images (t1,t1gd,t2,t2-flair), and tumor segmentation mask. 

- src/data: model and atlases
  - Atlas_Sur_NatMed.nii.gz: The 4th 3D channel includes the Overall Survival Map (OSM) atlas described in the manuscript.
  - jakob_stripped_with_cere_lps_256256128.nii.gz: common atlas where all images are deformed to
  - templateallregions.nii.gz: segmentation labels of the common atlas
- src/libs: matlab libraries

### Software requirements

- MATLAB version 9.4 (R2018a)

- greedy: https://github.com/pyushkevich/greedy [1]

- python3: For pdf report creation. Dependencies in src/python_dependencies


### Online platform
Link coming soon

### Image preprocessing

Codes for the image preprocessing are available separately through the following GitHub repositories
- Preprocessing pipeline (dicom to nifti conversion, image co-registration to the SRI atlas, and ptional brain extraction and tumor segmentation): https://github.com/CBICA/CaPTk [2]

- Brain extraction: https://github.com/CBICA/BrainMaGe [3]

- Tumor segmentation: https://github.com/FETS-AI/Front-End [4].


### References
[1]   Yushkevich, P.A., Pluta, J., Wang, H., Wisse, L.E., Das, S. and Wolk, D., 2016. Fast Automatic Segmentation of Hippocampal Subfields and Medial Temporal Lobe Subregions in 3 Tesla and 7 Tesla MRI. Alzheimer's & Dementia: The Journal of the Alzheimer's Association, 12(7), pp.P126-P127.

[2] Davatzikos et al. Cancer imaging phenomics toolkit: quantitative imaging analytics for precision diagnostics and predictive modeling of clinical outcome, J Med Imaging, 5(1):011018, 2018

[3] Thakur, S., et al. Brain extraction on MRI scans in presence of diffuse glioma: Multi-institutional performance evaluation of deep learning methods and robust modality-agnostic training. NeuroImage 220, 117081 (2020).

[4] Pati, S., et al. The federated tumor segmentation (FeTS) tool: an open-source solution to further solid tumor research. Physics in Medicine & Biology (2022).
