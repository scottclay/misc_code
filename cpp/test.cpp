#include <iostream>

class Dust {
	public:
		float Cb;
		float N;
		float O;
	//private:
	//	float total;
};

class Metals {
	public:
		float Cb;
		float N;
		float O;
		float print_metallicity(void);
	private:
		float metallicity(void);
};

float Metals::metallicity(void) {
	return Cb + N + O;
	}
float Metals::print_metallicity(void) {
	return metallicity();
	}


float add(float a, float b) {
	return (a+b);
	}

int main() {
	using namespace std;
	float total_dust, total_dust2;
	Dust ISM = {0.5, 1.5, 2.5};
	cout << "Hello World!" << std::endl;
	
	cout << "A + B = " << add(3.1, 4.6) << endl;
	
	
	total_dust = ISM.Cb + ISM.N + ISM.O;
	
	Metals IGM;
	
	IGM.Cb = 1.0;
	IGM.N  = 2.0;
	IGM.O  = 3.0;
	
	float metallicity = IGM.print_metallicity();
	
	cout << metallicity << endl;
	
	string str = "Scott";
	string str_reverse;
	for(int i=0; i<str.size()+1; i++) {
		str_reverse += str[str.size() - i];
	}
		
	
	cout << str << "\t" << str.size() << "\t" << str_reverse << endl;
	
	
	
	cout << total_dust << endl;
	
	
	
	return 0;
	}
	
	
	
	
	
	
	
	
	
	