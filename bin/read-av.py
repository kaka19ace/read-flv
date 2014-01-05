#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (c) 2014 Zhong Kaixiang
#
#  This file is simple parser for flv file 
#
import sys, os 

root_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../")
sys.path.insert(0, root_dir)

from readav import readav_main
if __name__ == '__main__':
    # -i infile -o outfile
    # other option

    infile_name = ""
    outfile_name = ""
    readav_main(intfile_name, outfile_name)







