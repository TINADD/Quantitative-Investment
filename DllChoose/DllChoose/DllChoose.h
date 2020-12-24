#pragma once
#define TESTCPPDLL_API __declspec(dllexport)
extern "C" TESTCPPDLL_API void _stdcall choose(const float para[11]);

#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstring>
#include <vector>
#include  <direct.h>  
#include  <stdio.h> 
#include <string>
#include <cmath>
#include <Windows.h> 


using namespace std;

struct TcsvMake
{
	string date;
	int code;
	float open;
	float high;
	float close;
	float settlement; //pre_close
	float vol;
	float mean_price;
	int amount;
	float changepercent;
	float turnover;
	float top10sh; //hold_ratio
	float top10sh_d;
	string industry;
	float totals;
	int PeriodToMar;
	int cq_sign;
	//double hl_diff;
};
typedef vector<TcsvMake> LISTcsvMake;

class CFileRead
{

public:
	//CFileRead();
	//virtual ~CFileRead();

	void readCSV(ifstream &input);
	//void choose(const float para[11]);

	LISTcsvMake m_csvMakeList;

};


