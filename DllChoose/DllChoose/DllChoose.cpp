// DllChoose.cpp: 定义 DLL 应用程序的导出函数。
//

#include "stdafx.h"
#include "DllChoose.h"

using namespace std;

template <class Type>
Type stringToNum(const string str) {
	istringstream iss(str);
	Type num;
	iss >> num;
	return num;
}

void CFileRead::readCSV(ifstream &input)
{
	string de = ",";
	string csvLine;// 从输入流中读取每一行
	getline(input, csvLine);
	while (getline(input, csvLine))
	{
		TcsvMake tcsv;
		//cout << csvLine << endl;
		if ("" == csvLine)
		{
			continue;
		}
		//方便截取最后一段数据
		std::string strs = csvLine + de;
		size_t pos = strs.find(de);
		size_t size = strs.size();

		std::string x = strs.substr(0, pos);
		istringstream csvStream(x);
		csvStream >> tcsv.date;
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string code = strs.substr(0, pos);
		tcsv.code = stringToNum<int>(code);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string open = strs.substr(0, pos);
		tcsv.open = stringToNum<float>(open);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string high = strs.substr(0, pos);
		tcsv.high = stringToNum<float>(high);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string close = strs.substr(0, pos);
		tcsv.close = stringToNum<float>(close);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string settlement = strs.substr(0, pos);
		tcsv.settlement = stringToNum<float>(settlement);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string vol = strs.substr(0, pos);
		tcsv.vol = stringToNum<float>(vol);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string mean_price = strs.substr(0, pos);
		tcsv.mean_price = stringToNum<float>(mean_price);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string amount = strs.substr(0, pos);
		tcsv.amount = stringToNum<int>(amount);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string changepercent = strs.substr(0, pos);
		tcsv.changepercent = stringToNum<float>(changepercent);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string turnover = strs.substr(0, pos);
		tcsv.turnover = stringToNum<float>(turnover);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string top10sh = strs.substr(0, pos);
		tcsv.top10sh = stringToNum<float>(top10sh);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string top10sh_d = strs.substr(0, pos);
		tcsv.top10sh_d = stringToNum<float>(top10sh_d);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string ind = strs.substr(0, pos);
		istringstream CSVSTREAM(ind);
		CSVSTREAM >> tcsv.industry;
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string totals = strs.substr(0, pos);
		tcsv.totals = stringToNum<float>(totals);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string PeriodToMar = strs.substr(0, pos);
		tcsv.PeriodToMar = stringToNum<int>(PeriodToMar);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		string cq_sign = strs.substr(0, pos);
		tcsv.cq_sign = stringToNum<int>(cq_sign);
		strs = strs.substr(pos + 1, size);
		pos = strs.find(de);

		//string hl_diff = strs.substr(0, pos);
		//tcsv.hl_diff = stringToNum<int>(cq_sign);
		//strs = strs.substr(pos + 1, size);
		//pos = strs.find(de);

		m_csvMakeList.push_back(tcsv);
	}

}


//windows下获取当前dll的句柄
HMODULE GetSelfModuleHandle()
{
	MEMORY_BASIC_INFORMATION mbi;
	return ((::VirtualQuery(GetSelfModuleHandle, &mbi, sizeof(mbi)) != 0) ? (HMODULE)mbi.AllocationBase : NULL);
}
//在程序中通过调用该函数即可获取到dll的完整路径至strDllFullPath中
void GetFullPathOfDll(std::string& strDllFullPath)
{
	char szPath[MAX_PATH];
	GetModuleFileNameA(GetSelfModuleHandle(), szPath, MAX_PATH);
	strDllFullPath = std::string(szPath);
}


void __stdcall choose(const float para[12])
{
	/*
	para[0]:policy1_list 0.03
	para[1]:policy2_list 1
	para[2]:policy3_list 10
	para[3]:tr_list 2
	para[4]:cp_up_list 8
	para[5]:cp_down_list 4
	para[6]:top10sh_list 50
	para[7]:totals1_down_list 30
	para[8]:totals1_up_list 300
	para[9]:price_up_list 40
	para[10]:price_down_list 4
	para[11]: hl_diff 0.18
	*/
	//char exeFullPath[MAX_PATH]; // Full path
	string strPath = "";

	//GetModuleFileNameA(NULL, exeFullPath, MAX_PATH);
	//GetModuleFileName(NULL, exeFullPath, MAX_PATH);
	GetFullPathOfDll(strPath);    // Get full path of the file
	size_t pos = strPath.find_last_of('\\', strPath.length());
	string p_dir = strPath.substr(0, pos);
	string read_f = "\\daily_data.csv";
	string str_r = p_dir + read_f;
	//cout << str_r << endl;
	CFileRead readTest1;
	ifstream fin(str_r);
	if (!fin)
	{
		cout << "can not open!" << endl;
	}
	else {
		readTest1.readCSV(fin);
	}
	int c[1] = { 0 };
	vector<int> code_list(c, c + 1);
	vector<int> return_list(c, c + 1);
	float highest, cp_sum, policy3, policy2, policy1, close, tr, top10, totals, tmp1, tmp2, tmp3, hl_diff;
	float vol_before;
	int period = 1, code;

	for (size_t i = 0; i <= readTest1.m_csvMakeList.size() - 1; i += period)
	{
		if (i >= readTest1.m_csvMakeList.size() || i < 0)
		{
			//cout << "vetcor下标越界" << endl;
			break;
		}
		if (readTest1.m_csvMakeList[i].code != code_list.back())
		{
			size_t j = i;
			code = readTest1.m_csvMakeList[i].code;
			code_list.push_back(code);
			close = readTest1.m_csvMakeList[i].close;
			tr = readTest1.m_csvMakeList[i].turnover;
			top10 = readTest1.m_csvMakeList[i].top10sh;
			totals = readTest1.m_csvMakeList[i].totals;
			//hl_diff = readTest1.m_csvMakeList[i].hl_diff;

			highest = 0.0; //记录前30天收盘最高价
			for (j = i; (j < i + 22) && (readTest1.m_csvMakeList[j].code == code); j++) {
				if (j >= readTest1.m_csvMakeList.size() || j < 0)
				{
					/*cout << "vetcor下标越界" << endl;
					cout << i << endl;
					cout << j << endl;*/
					break;
				}
				highest = max(readTest1.m_csvMakeList[j].close, highest);
			}
			vol_before = readTest1.m_csvMakeList[i + 1].vol; //下载的数据按日期降序排列，所以是i+1

															 //policy3:买入前两天到达的涨幅
			tmp1 = max(readTest1.m_csvMakeList[i].close, readTest1.m_csvMakeList[i + 1].close);
			tmp2 = min(readTest1.m_csvMakeList[i].open, readTest1.m_csvMakeList[i + 1].open);
			policy3 = (tmp1 - tmp2) / tmp2 * 100.0;

			//cp_sum: 买入前五天的涨幅
			tmp3 = readTest1.m_csvMakeList[i].changepercent + readTest1.m_csvMakeList[i + 1].changepercent + \
				readTest1.m_csvMakeList[i + 2].changepercent;
			cp_sum = tmp3 + readTest1.m_csvMakeList[i + 3].changepercent + readTest1.m_csvMakeList[i + 4].changepercent;

			//policy1:收盘价与前30天包括选股当天的最高收盘价差值比例
			policy1 = (highest - close) / close;

			//policy2:选股当天成交量大于昨日成交量*1
			policy2 = readTest1.m_csvMakeList[i].vol / vol_before;

			if ((policy1 < para[0]) && (policy2 > para[1]) && (policy3 < para[2]) && (tr > para[3]) && (para[5] < cp_sum && cp_sum < para[4])\
				&& (top10 >= para[6]) && (para[7] < totals && totals < para[8]) && (para[9] < close && close < para[10]))
			{
				cout << readTest1.m_csvMakeList[i].code << endl;
				cout << policy1 << " " << para[0] << endl;
				cout << policy2 << " " << para[1] << endl;
				cout << policy3 << " " << para[2] << endl;
				cout << tmp1 << tmp2 << endl;
				cout << tr << " " << para[3] << endl;
				cout << para[4] << " " << cp_sum << " " << para[5] << endl;
				cout << top10 << " " << para[6] << endl;
				cout << para[7] << " " << totals << " " << para[8] << endl;
				cout << para[9] << " " << close << " " << para[10] << endl;
				return_list.push_back(readTest1.m_csvMakeList[i].code);
			}
			if (code == 987)
			{
				cout << code << " " << i << " " << j << endl;
			}
			period = j - i;
		}
		else
			period = 1;
		continue;
	}
	cout << readTest1.m_csvMakeList[1].code << endl;
	fin.close();

	string to_dir = "\\data.csv";
	string str_to_r = p_dir + to_dir;
	ofstream outFile1;
	outFile1.open(str_to_r); // 打开模式可省略 
	outFile1 << "code" << endl;
	for (size_t m = 1; m <= return_list.size() - 1; m++) {
		if (m >= return_list.size() || m < 0)
		{
			//cout << "vetcor下标越界" << endl;
			break;
		}
		outFile1 << return_list[m] << endl;
	}
	outFile1.close();
}




