#!/bin/bash

echo "Testing Monthly Profile Endpoint"
echo "-------------------------------"
curl -X GET "http://localhost:8000/weather/monthly-profile?city=Ldon&month=7"
echo -e "\n"

echo "Testing Best Month Endpoint"
echo "-------------------------"
curl -X GET "http://localhost:8000/travel/best-month?city=Ldon&min_temp=15&max_temp=25"
echo -e "\n"

echo "Testing Compare Cities Endpoint"
echo "-----------------------------"
curl -X GET "http://localhost:8000/travel/compare-cities?cities=New%20Yk,Tokyo,Sydney&month=4"
echo -e "\n"

echo "Testing Metrics Endpoint"
echo "----------------------"
curl -X GET "http://localhost:8000/metrics"
echo -e "\n"

