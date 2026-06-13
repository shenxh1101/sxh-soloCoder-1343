package com.example.sample;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeoutException;

/**
 * 样本Java模块，用于测试文档生成器。
 * 
 * 这个包包含了各种Java代码结构，包括类、接口、
 * 枚举、泛型和Javadoc注释。
 * 
 * @author Test Author
 * @version 1.0.0
 * @since 1.0.0
 */
public class SampleModule {

    /**
     * 一个简单的计算器类，支持基本的数学运算。
     * 
     * @author Test Author
     * @version 1.0.0
     * @see MathUtil
     */
    public static class Calculator {
        private int precision;
        private double memory;

        /**
         * 初始化计算器。
         * 
         * @param precision 计算结果的小数位数，默认为2
         */
        public Calculator(int precision) {
            this.precision = precision;
            this.memory = 0.0;
        }

        /**
         * 默认构造函数，精度为2。
         */
        public Calculator() {
            this(2);
        }

        /**
         * 两个数相加。
         * 
         * @param a 第一个加数
         * @param b 第二个加数
         * @return 两数之和
         * 
         * <pre>{@code
         * Calculator calc = new Calculator();
         * double result = calc.add(2, 3); // returns 5.0
         * }</pre>
         */
        public double add(double a, double b) {
            return Math.round((a + b) * Math.pow(10, precision)) / Math.pow(10, precision);
        }

        /**
         * 两个数相除。
         * 
         * @param a 被除数
         * @param b 除数
         * @return 两数之商
         * @throws ArithmeticException 当除数为0时抛出
         * 
         * <pre>{@code
         * Calculator calc = new Calculator();
         * double result = calc.divide(10, 2); // returns 5.0
         * }</pre>
         */
        public double divide(double a, double b) throws ArithmeticException {
            if (b == 0) {
                throw new ArithmeticException("除数不能为零");
            }
            return Math.round((a / b) * Math.pow(10, precision)) / Math.pow(10, precision);
        }

        /**
         * 获取当前内存中的值。
         * @return 内存中的值
         */
        public double getMemory() {
            return memory;
        }

        /**
         * 设置内存中的值。
         * @param value 要存储的值
         */
        public void setMemory(double value) {
            this.memory = value;
        }
    }

    /**
     * 数学工具类，提供常用的数学函数。
     */
    public static class MathUtil {
        /**
         * 生成斐波那契数列。
         * 
         * @param n 要生成的数列长度
         * @return 斐波那契数列
         * @throws IllegalArgumentException 当n小于0时抛出
         */
        public static List<Integer> fibonacci(int n) {
            if (n < 0) {
                throw new IllegalArgumentException("n不能为负数");
            }
            
            List<Integer> result = new ArrayList<>();
            if (n == 0) return result;
            if (n == 1) {
                result.add(0);
                return result;
            }
            
            result.add(0);
            result.add(1);
            for (int i = 2; i < n; i++) {
                result.add(result.get(i-1) + result.get(i-2));
            }
            return result;
        }
    }

    /**
     * 用户接口定义。
     */
    public interface User {
        /**
         * 获取用户ID。
         * @return 用户ID
         */
        int getId();
        
        /**
         * 获取用户名。
         * @return 用户名
         */
        String getName();
        
        /**
         * 获取用户邮箱。
         * @return 用户邮箱
         */
        String getEmail();
    }

    /**
     * 用户角色枚举。
     */
    public enum Role {
        /** 普通用户 */
        USER,
        /** 管理员 */
        ADMIN,
        /** 访客 */
        GUEST
    }

    /**
     * 生成问候语。
     * 
     * @param name 要问候的人的名字
     * @param greeting 问候语
     * @return 完整的问候语字符串
     */
    public static String greet(String name, String greeting) {
        return greeting + ", " + name + "!";
    }

    /**
     * 生成问候语（默认问候语）。
     * 
     * @param name 要问候的人的名字
     * @return 完整的问候语字符串
     */
    public static String greet(String name) {
        return greet(name, "Hello");
    }

    /**
     * 异步获取数据（示例）。
     * 
     * @param url 数据的URL地址
     * @param timeout 超时时间（秒）
     * @return 解析后的JSON数据
     * @throws TimeoutException 当请求超时时抛出
     */
    public static Map<String, Object> fetchData(String url, int timeout) throws TimeoutException {
        throw new UnsupportedOperationException("示例方法，未实现");
    }
}
