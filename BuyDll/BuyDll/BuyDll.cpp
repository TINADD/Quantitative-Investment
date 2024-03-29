// buy_dll.cpp : 定义 DLL 应用程序的导出函数。
//

#include "stdafx.h"

extern "C"
{
	__declspec(dllexport)
		//arr1 - settlement—昨日收盘价,mean_price_before—昨日均价,30_close_highest—30天最高价,open_price—当天开盘价
		//arr2 - 买入参数 eg:1.01， 0.97， 0.99  定值
		void buy(const float arr1[4], const float arr2[10], float &bprice, float &bpolicy)
	{
		//open>=settlement 如果开盘<昨日收盘*1.01 则开盘直接买入--策略2 否则以昨日收盘*1.01买入 -- 策略1
		if (arr1[3] >= arr1[0]) {
			if (arr1[3] <= arr1[0] * arr2[0]) {
				bprice = arr1[3];
				bpolicy = 2.0;
			}
			else {
				bprice = arr1[0] * arr2[0];
				bpolicy = 1.0;
			}
		}
		//open<settlement if open>=0.97*highest -- policy_4_value(--policy3)/open--policy4 else policy_5_value -- policy5
		else {
			float policy_4_value = min(arr1[0], arr1[1]);
			float policy_5_value = max(arr1[0], arr1[1], arr1[2] * arr2[2]);
			if (arr1[3] >= arr2[1] * arr1[2]) {
				if (arr1[3] <= policy_4_value) {
					bprice = arr1[3];
					bpolicy = 4.0;
				}
				else {
					bprice = arr2[1] * arr1[2];
					bpolicy = 3.0;
				}
			}
			else {
				bprice = policy_5_value;
				bpolicy = 5.0;
			}
		}
	}

}

//卖出定上下界
extern "C"
{
	__declspec(dllexport)
		void decision_sp_ub(const float arr1[3], const float arr2[10], float &lb, float &ub)
	{
		float bp = arr1[0];
		float op = arr1[1];
		float cp = arr1[2];
		float a_up100 = arr2[0];
		float b_up100 = arr2[1];
		float c = arr2[2];
		if (op >= bp) {
			lb = max(bp, (op + a_up100 * bp));
			ub = min((cp + c * cp), (bp + c * bp), (op + b_up100 * bp));
		}
		else {
			lb = op + a_up100 * bp;
			ub = max(bp, (op + b_up100 * bp));
		}
	}

}


