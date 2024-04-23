#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import os
from zipfile import ZipFile
import tempfile
from bio_parser.utils import check_valid_bio
from pathlib import Path
import shutil

def validate_data(gtFilePath, submFilePath, evaluationParams):
    """
    Method validate_data: validates that all files in the results folder are correct (have the correct name contents).
                            Validates also that there are no missing files in the folder.
                            If some error detected, raise the error
    
    Types of errors contemplated:
    - Submissions file is missing files for the samples
    - Submissions file has more files than expected
    - Files do not have .bio extension
    - .bio files have problems when being loaded by the bio parser
    """

    #GT directory with .bio files
    try:
        gt_dir = tempfile.mkdtemp()
        gt_zip = ZipFile(gtFilePath, "r")
        gt_zip.extractall(path=gt_dir)
    except:
        shutil.rmtree(gt_dir)
        raise Exception("Error unpacking GT data, contact the administrator.")

    #Directory to store user submission
    try:
        hyp_dir = tempfile.mkdtemp()
        hyp_zip = ZipFile(submFilePath, "r")
        hyp_zip.extractall(path=hyp_dir)
    except:
        shutil.rmtree(hyp_dir)
        raise Exception("Error unpacking your submission, are you sure you sent a .zip file?")    
    
    #Tests to validate data
    gt_files = os.listdir(path=gt_dir)
    gt_files.sort()
    hyp_files = os.listdir(path=hyp_dir)
    hyp_files.sort()

    #We no longer need anything from gt files
    shutil.rmtree(gt_dir) 

    #Test 1: Filename lists match
    if gt_files != hyp_files:
        if len(hyp_files) < len(gt_files):
            raise Exception("The submission has fewer files than expected. Remember to generate one .bio file for each test sample image.")
        elif len(hyp_files) > len(gt_files):
            raise Exception("The submission has more files than expected. Make sure only .bio files are included (one for each test sample image).")
        else:
            raise Exception("An error has occured. The file names should match the image IDs and the extension should be .bio")

    #Test 2: Validate .bio format with bio parser (it will throw an exception if something is wrong)
    try:
        hyp_files_with_abs_path = [Path(os.path.join(hyp_dir, f)) for f in hyp_files]
        check_valid_bio(hyp_files_with_abs_path)
    except Exception as exc:
        shutil.rmtree(hyp_dir)
        raise

    shutil.rmtree(hyp_dir)

    

def evaluate_method(gtFilePath, submFilePath, evaluationParams):
    """
    Method evaluate: evaluate the submited method and fill the output dictionary
    """

    # Dict with per sample results (Optional)
    #perSampleMetrics = {}

    #Dict with all metrics, initialized to lowest score
    methodMetrics = dict()
    methodMetrics["ecer"] = 100.0
    methodMetrics["ewer"] = 100.0
    methodMetrics["nerval-f1"] = 0.0
    methodMetrics["nerval-p"] = 0.0
    methodMetrics["nerval-r"] = 0.0
    
    #GT directory with .bio files
    try:
        gt_dir = tempfile.mkdtemp()
        gt_zip = ZipFile(gtFilePath, "r")
        gt_zip.extractall(path=gt_dir)
    except:
        shutil.rmtree(gt_dir)
        raise Exception("Error unpacking GT data, contact the administrator.")

    #Directory to store user submission
    try:
        hyp_dir = tempfile.mkdtemp()
        hyp_zip = ZipFile(submFilePath, "r")
        hyp_zip.extractall(path=hyp_dir)
    except:
        shutil.rmtree(hyp_dir)
        raise Exception("Error unpacking your submission, are you sure you sent a .zip file?")


    try:
        ecer_ewer_output = os.popen("ie-eval ecer-ewer --label-dir {}/ --prediction-dir {}/".format(gt_dir, hyp_dir))
        ecer_ewer_results_line = ecer_ewer_output.readlines()[-1].strip()
        [ecer, ewer] = ecer_ewer_results_line.split("|")[2:4]
        ecer = float(ecer.strip())
        ewer = float(ewer.strip())

        nerval_output = os.popen("ie-eval nerval --label-dir {}/ --prediction-dir {}/ --nerval-threshold 30.0".format(gt_dir, hyp_dir))
        nerval_results_line = nerval_output.readlines()[-1].strip()
        [nerval_p, nerval_r, nerval_f1] = nerval_results_line.split("|")[2:5]
        nerval_p = float(nerval_p.strip())
        nerval_r = float(nerval_r.strip())
        nerval_f1 = float(nerval_f1.strip())

        methodMetrics["ecer"] = ecer
        methodMetrics["ewer"] = ewer
        methodMetrics["nerval-f1"] = nerval_f1
        methodMetrics["nerval-p"] = nerval_p
        methodMetrics["nerval-r"] = nerval_r

        shutil.rmtree(gt_dir)
        shutil.rmtree(hyp_dir)
    except:
        shutil.rmtree(gt_dir)
        shutil.rmtree(hyp_dir)
        raise Exception("Something went wrong during the evaluation, did you validate the data?")
    finally:
        resDict = {'result':True,'msg':'','method': methodMetrics}
        return resDict
