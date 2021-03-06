#!/usr/bin/env python
#-*- coding:utf-8 -*-

#CLAM wrapper script for PICCL

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#This wrapper script uses Python and the CLAM Data API.
#We make use of the XML settings file that CLAM outputs, rather than
#passing all parameters on the command line.


#If we run on Python 2.7, behave as much as Python 3 as possible
from __future__ import print_function, unicode_literals, division, absolute_import

#import some general python modules:
import sys
import os
import glob
import shutil
import locale

#import CLAM-specific modules. The CLAM API makes a lot of stuff easily accessible.
import clam.common.data
import clam.common.status

#When the wrapper is started, the current working directory corresponds to the project directory, input files are in input/ , output files should go in output/ .

#make a shortcut to the shellsafe() function
shellsafe = clam.common.data.shellsafe

#this script takes three arguments from CLAM: $DATAFILE $STATUSFILE $OUTPUTDIRECTORY
#(as configured at COMMAND= in the service configuration file, there you can
#reconfigure which arguments are passed and in what order.
datafile = sys.argv[1]
statusfile = sys.argv[2]
inputdir = sys.argv[3]
outputdir = sys.argv[4]
piccldataroot = sys.argv[5]
if len(sys.argv) >= 7:
    #use scripts from src/ directly
    run_piccl = sys.argv[6]
    if run_piccl[-1] != '/': run_piccl += "/"
    print("Running PICCL from " + run_piccl,file=sys.stderr)
else:
    #use the piccl nextflow downloads (this is not very well supported/tested currently!)
    run_piccl = "nextflow run LanguageMachines/PICCL/"
    print("Running PICCL mediated by Nextflow",file=sys.stderr)


print("Virtual Environment: ", os.environ.get('VIRTUAL_ENV', "(none)"), file=sys.stderr)
print("System default encoding: ", sys.getdefaultencoding(), file=sys.stderr)
print("Forcing en_US.UTF-8 locale...", file=sys.stderr)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

#If you make use of CUSTOM_FORMATS, you need to import your service configuration file here and set clam.common.data.CUSTOM_FORMATS
#Moreover, you can import any other settings from your service configuration file as well:

#from yourserviceconf import CUSTOM_FORMATS

#Obtain all data from the CLAM system (passed in $DATAFILE (clam.xml)), always pass CUSTOM_FORMATS as second argument if you make use of it!
clamdata = clam.common.data.getclamdata(datafile)

if 'debug' in clamdata and clamdata['debug']:
    print("Locale information (will force en_US.UTF-8): ", file=sys.stderr)
    os.system("locale >&2")
    print("Nextflow: ", file=sys.stderr)
    os.system("which nextflow >&2")
    print("NXF_HOME: ", os.environ.get('NXF_HOME', "(none)"), file=sys.stderr)
    print("LM_PREFIX: ", os.environ.get('LM_PREFIX', "(none)"), file=sys.stderr)

#You now have access to all data. A few properties at your disposition now are:
# clamdata.system_id , clamdata.project, clamdata.user, clamdata.status , clamdata.parameters, clamdata.inputformats, clamdata.outputformats , clamdata.input , clamdata.output

clam.common.status.write(statusfile, "Starting...")

def fail(prefix=None):
    if prefix:
        nextflowout(prefix)
    if os.path.exists('work'):
        if 'debug' not in clamdata or not clamdata['debug']:
            shutil.rmtree('work')
    sys.exit(1)

def nextflowout(prefix):
    print("[" + prefix + "] Nextflow standard error output",file=sys.stderr)
    print("-------------------------------------------------",file=sys.stderr)
    print(open(prefix+'.nextflow.err.log','r',encoding='utf-8').read(), file=sys.stderr)
    os.unlink(prefix+'.nextflow.err.log')

    print("[" + prefix + "] Nextflow standard output",file=sys.stderr)
    print("-------------------------------------------------",file=sys.stderr)
    print(open(prefix+'.nextflow.out.log','r',encoding='utf-8').read(), file=sys.stderr)
    os.unlink(prefix+'.nextflow.out.log')

    if os.path.exists('trace.txt'):
        print("[" + prefix + "] Nextflow trace summary",file=sys.stderr)
        print("-------------------------------------------------",file=sys.stderr)
        print(open('trace.txt','r',encoding='utf-8').read(), file=sys.stderr)
        os.unlink('trace.txt')

def publish(d, extension="xml"):
    """publish files from directory d to the output directory by symlinking"""
    for filename in glob.glob(os.path.join(d,'*.' + extension)):
        os.symlink(os.path.abspath(filename), os.path.join(outputdir, os.path.basename(filename)))

#=========================================================================================================================

lang = clamdata['lang']
if lang == 'deu_frak': lang = 'deu' #Fraktur German is german for all other intents and purposes

if 'frog' in clamdata and clamdata['frog']:
    if lang != 'nld':
        print("Input document is not dutch (got + " + str(lang) + "), defiantly ignoring linguistic enrichment choice!",file=sys.stderr)

datadir = os.path.join(piccldataroot,'data','int',lang)
if not os.path.exists(datadir):
    errmsg = "ERROR: Unable to find data files for language '" + lang + "' in path " + piccldataroot
    clam.common.status.write(statusfile, errmsg,0) # status update
    print(errmsg,file=sys.stderr)
    sys.exit(4)

#has an explicit lexicon been provided already?
have_lexicon = os.path.exists(inputdir + "/lexicon.lst")
if not os.path.exists("lexicon.lst") and have_lexicon:
    os.symlink(inputdir+"/lexicon.lst", 'lexicon.lst')

#loop over all data files and copy (symlink actually to save diskspace and time) to the current working directory (project dir)
for f in glob.glob(datadir + '/*'):
    if f.split('.')[-1] == 'dict' and not have_lexicon:
        if os.path.exists('lexicon.lst'): os.unlink('lexicon.lst') #remove any existing
        try:
            os.symlink(f, 'lexicon.lst')
        except Exception as e:
            print(str(e),file=sys.stderr)
    if f.split('.')[-1] == 'chars':
        if os.path.exists('alphabet.lst'): os.unlink('alphabet.lst') #remove any existing
        try:
            os.symlink(f, 'alphabet.lst')
        except Exception as e:
            print(str(e),file=sys.stderr)
    if f.split('.')[-1] == 'confusion':
        if os.path.exists('confusion.lst'): os.unlink('confusion.lst') #remove any existing
        try:
            os.symlink(f, 'confusion.lst')
        except Exception as e:
            print(str(e),file=sys.stderr)

if not os.path.exists('lexicon.lst'):
    errmsg = "ERROR: Unable to find lexicon file for language '" + lang + "' in path " + piccldataroot
    clam.common.status.write(statusfile, errmsg,0) # status update
    print(errmsg,file=sys.stderr)
    sys.exit(4)
if not os.path.exists('alphabet.lst'):
    errmsg = "ERROR: Unable to find alphabet file for language '" + lang + "' in path " + piccldataroot
    clam.common.status.write(statusfile, errmsg,0) # status update
    print(errmsg,file=sys.stderr)
    sys.exit(4)
if not os.path.exists('confusion.lst'):
    errmsg = "ERROR: Unable to find confusion file for language '" + lang + "' in path " + piccldataroot
    clam.common.status.write(statusfile, errmsg,0) # status update
    print(errmsg,file=sys.stderr)
    sys.exit(4)


#Derive input type from used inputtemplate
inputtype = ''
for inputfile in clamdata.input:
    inputtemplate = inputfile.metadata.inputtemplate
    if inputtemplate in ('pdfimages', 'pdftext', 'tif','jpg','png','gif','foliaocr','textocr'):
        inputtype = inputtemplate

if not inputtype:
    errmsg = "ERROR: Unable to deduce input type on the basis of input files (should not happen)!"
    clam.common.status.write(statusfile, errmsg,0) # status update
    print(errmsg,file=sys.stderr)
    sys.exit(5)

if inputtype == 'foliaocr':
    ticclinputdir = "." #FoLiA input files provided directly, no need to run OCR pipeline
    ticcl_inputtype = "folia"
elif inputtype == 'textocr':
    ticclinputdir = "." #FoLiA input files provided directly, no need to run OCR pipeline
    ticcl_inputtype = "text"
elif inputtype == 'pdftext':
    ticclinputdir = "." #FoLiA input files provided directly, no need to run OCR pipeline
    ticcl_inputtype = "pdf"
else:
    #run the OCR pipeline prior to running TICCL
    clam.common.status.write(statusfile, "Running OCR Pipeline",1) # status update

    ocr_outputdir = "ocr_output"

    cmd = run_piccl + "ocr.nf --inputdir " + shellsafe(inputdir,'"') + " --outputdir " + shellsafe(ocr_outputdir,'"') + " --inputtype " + shellsafe(inputtype,'"') + " --language " + shellsafe(clamdata['lang'],'"') +" -with-trace >ocr.nextflow.out.log 2>ocr.nextflow.err.log"
    print("Command: " + cmd, file=sys.stderr)
    if os.system(cmd) != 0: #use original clamdata['lang'] (may be deu_frak)
        fail('ocr')


    #Print Nextflow information to stderr so it ends up in the CLAM error.log and is available for inspection
    nextflowout('ocr')

    #make output files available
    publish(ocr_outputdir)

    ticclinputdir = ocr_outputdir
    ticcl_inputtype = "folia"

pdfhandling = 'reassemble' if 'reassemble' in clamdata and clamdata['reassemble'] else 'single'

if 'frog' in clamdata and clamdata['frog'] == 'yes':
    print("Frog enabled (" + str(clamdata['frog']) + ")",file=sys.stderr)

if 'ticcl' in clamdata and clamdata['ticcl'] == 'yes':
    clam.common.status.write(statusfile, "Running TICCL Pipeline",50) # status update
    ticcl_outputdir = 'ticcl_out'
    cmd = run_piccl + "ticcl.nf --inputdir " + ticclinputdir + " --inputtype " + ticcl_inputtype + " --outputdir " + shellsafe(ticcl_outputdir,'"') + " --lexicon lexicon.lst --alphabet alphabet.lst --charconfus confusion.lst --clip " + shellsafe(clamdata['rank']) + " --distance " + shellsafe(clamdata['distance']) + " --clip " + shellsafe(clamdata['rank']) + " --pdfhandling " + pdfhandling + " -with-trace >ticcl.nextflow.out.log 2>ticcl.nextflow.err.log"
    print("Command: " + cmd, file=sys.stderr)
    if os.system(cmd) != 0:
        fail('ticcl')

    #Print Nextflow information to stderr so it ends up in the CLAM error.log and is available for inspection
    nextflowout('ticcl')

    publish(ticcl_outputdir)

    frog_inputdir = ticcl_outputdir
    textclass_opts = ""
else:
    print("TICCL skipped as requested...",file=sys.stderr)
    frog_inputdir = ocr_outputdir
    textclass_opts = "--inputclass \"OCR\" --outputclass \"current\"" #extra textclass opts for both frog and/or ucto


frog = 'frog' in clamdata and clamdata['frog'] == 'yes' and lang == "nld"
if lang == "nld":
    for key in ('pos','lemma','morph','ner','parser','chunker'):
        if key in clamdata and clamdata[key]:
            frog = True #enable frog on the fly even if the user forgot to explicitly enable it
if frog:
    skip = ""
    #PoS can't be skipped
    if 'lemma' not in clamdata or not clamdata['lemma']:
        skip += 'l'
    if 'parser' not in clamdata or not clamdata['parser']:
        skip += 'mp'
    if 'morph' not in clamdata or not clamdata['morph']:
        skip += 'a'
    if 'ner' not in clamdata or not clamdata['ner']:
        skip += 'n'
    if 'chunker' not in clamdata or not clamdata['chunker']:
        skip += 'c'
    if skip:
        skip = "--skip=" + skip


if 'ucto' in clamdata and clamdata['ucto'] == 'yes':
    #fallback in case only tokenisation is enabled, no need for Frog but use ucto

    tok_output = "tok_output"
    if not os.path.exists(tok_output): os.mkdir(tok_output)
    clam.common.status.write(statusfile, "Running Tokeniser (ucto)",75) # status update
    cmd = run_piccl + "tokenize.nf " + textclass_opts + " --language " + shellsafe(lang,'"') + " --inputformat folia --inputdir " + shellsafe(frog_inputdir,'"') + " --extension folia.xml --outputdir " + shellsafe(tok_output,'"') + " -with-trace >ucto.nextflow.out.log 2>ucto.nextflow.err.log"
    print("Command: " + cmd, file=sys.stderr)
    if os.system(cmd) != 0:
        fail('ucto')
    nextflowout('ucto')
    publish(tok_output)

if frog:
    #is Frog selected?
    frog_output = "frog_output"
    if not os.path.exists(frog_output): os.mkdir(frog_output)
    print("Running Frog...",file=sys.stderr)
    clam.common.status.write(statusfile, "Running Frog Pipeline (linguistic enrichment)",75) # status update
    cmd = run_piccl + "frog.nf " + textclass_opts + " " + skip + " --inputdir " + shellsafe(frog_inputdir,'"') + " --inputformat folia --extension folia.xml --outputdir " + shellsafe(frog_output,'"') + " -with-trace >frog.nextflow.out.log 2>frog.nextflow.err.log"
    print("Command: " + cmd, file=sys.stderr)
    if os.system(cmd) != 0:
        fail('frog')
    nextflowout('frog')
    publish(frog_output)

#PICCL produces concatenative output filenames (e.g  $documentbase.ocr.ticcl.frogged.folia.xml)
#this goes beyond CLAM's ability to predict so we rename everything to retain only the last three extension elements (*.$system.folia.xml)
for filename in glob.glob(os.path.join(outputdir,"*.folia.xml")):
    basename = os.path.basename(filename)
    newbasename = ".".join([ field for field in basename.split('.')[:-3] if field not in ('ticcl','ocr','tok','frogged','folia') ]) + "." + ".".join(basename.split('.')[-3:])
    if newbasename != basename:
        os.rename(filename, os.path.join(outputdir, newbasename))


#cleanup
if 'debug' not in clamdata or not clamdata['debug']:
    shutil.rmtree('work')

#A nice status message to indicate we're done
clam.common.status.write(statusfile, "All done!",100) # status update

sys.exit(0) #non-zero exit codes indicate an error and will be picked up by CLAM as such!
