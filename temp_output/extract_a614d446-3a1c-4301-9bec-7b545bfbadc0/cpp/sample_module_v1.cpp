#include "sample_module.h"
#include <cmath>
#include <sstream>

namespace sample {

Calculator::Calculator(int precision) : precision(precision), memory(0.0) {}

double Calculator::add(double a, double b) const {
    double factor = std::pow(10, precision);
    return std::round((a + b) * factor) / factor;
}

double Calculator::divide(double a, double b) const {
    if (b == 0) {
        throw std::runtime_error("除数不能为零");
    }
    double factor = std::pow(10, precision);
    return std::round((a / b) * factor) / factor;
}

double Calculator::getMemory() const {
    return memory;
}

void Calculator::setMemory(double value) {
    memory = value;
}

std::vector<int> MathUtil::fibonacci(int n) {
    if (n < 0) {
        throw std::invalid_argument("n不能为负数");
    }
    
    std::vector<int> result;
    if (n == 0) return result;
    if (n == 1) {
        result.push_back(0);
        return result;
    }
    
    result.push_back(0);
    result.push_back(1);
    for (int i = 2; i < n; i++) {
        result.push_back(result[i-1] + result[i-2]);
    }
    return result;
}

std::string greet(const std::string& name, const std::string& greeting) {
    std::ostringstream oss;
    oss << greeting << ", " << name << "!";
    return oss.str();
}

std::map<std::string, std::string> fetchData(const std::string& url, int timeout) {
    throw std::runtime_error("示例方法，未实现");
}

} // namespace sample
