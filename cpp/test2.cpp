#include <iostream>
#include <string>

class Patient {
	public:
		std::string firstname;
		std::string surname;
		float age;
		void print_patient_data(void);
		void reverse_name(std::string);
};

void Patient::print_patient_data(void) {
	std::cout << "--------MEDICAL RECORD--------" << std::endl;
	std::cout << "Name: " << firstname <<" "<< surname <<std::endl;
	std::cout << "Age: " << age <<std::endl;
	std::cout << "------------------------------" <<std::endl <<std::endl;
}

void Patient::reverse_name(std::string str) {
	std::string str_reverse;
	for(int i=0; i<str.size()+1; i++) {
		str_reverse += str[str.size() - i];
	}
	std::cout << "Name in reverse: " << str_reverse << std::endl;
}



int main() {
	
	using namespace std;
	
	Patient human; 
	
	cout << "Please enter patient name (first and last): ";
	cin >> human.firstname >> human.surname; 	
	cout << endl;
	cout << "Please enter " << human.firstname << "'s age :";
	cin >> human.age;
	cout << endl;
	
	human.print_patient_data();
	
	cout << "Would you like to see " << human.firstname << "'s name in reverse?" << endl;
	cout << "Please enter Y or N :";
	string answer;
	cin >> answer;
	cout << endl;
	
	if(answer == "Y") {
		human.reverse_name(human.firstname);
	}
	else if (answer == "N") {
		cout << ":(" << endl;
	}
	else {
		cout << "You're cheating! Enter Y or N!" << endl;
	}
	
	
	
	return 0;
	}
	
	
	
	
	
	
	
	
	
	