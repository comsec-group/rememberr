#!/bin/bash

export ERRATA_ROOT=$(realpath "$0")

export ERRATA_ROOTDIR="${ERRATA_ROOT%/*}"

export ERRATA_BUILDDIR="${ERRATA_ROOTDIR}/build"

export ERRATA_PRINTPROGESS=1

mkdir -p $ERRATA_ROOTDIR/figures
