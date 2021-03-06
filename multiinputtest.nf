#!/usr/bin/env nextflow

/*
vim: syntax=groovy
-*- mode: groovy;-*-
*/


textdocuments = Channel.fromPath("*.txt")

process bulkprocessfiles {
    publishDir "testout"

    input:
    file alldocuments from textdocuments.collect()

    output:
    file "outputdir/*.txt" into textoutput

    """
    mkdir outputdir

    #next comes the actual work; this is just a silly example that could be
    #split into more atomic parts, but let's pretend it's a monolithic
    #unseparable meaningful action that transforms all input files on the basis
    #of all others and yields new output files for each
    cp *.txt outputdir/
    for f in outputdir/*; do
        mv \$f outputdir/test.\$(basename \$f)
    done
    """
}

textoutput.subscribe { println it }
