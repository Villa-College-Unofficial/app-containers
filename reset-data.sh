#!/bin/bash

sudo umount ./data/merged/*
sudo rm -rf ./data/merged/*
sudo rm -rf ./data/upper/*
sudo rm -rf ./data/work/*

ls -lah ./data/{merged,upper,work}