/**
 * 样本JavaScript模块，用于测试文档生成器。
 * 
 * 这个模块包含了各种JavaScript代码结构，包括类、
 * 函数、异步方法和JSDoc注释。
 * 
 * @module SampleModule
 * @author Test Author
 * @version 1.0.0
 */

/**
 * 一个简单的计算器类，支持基本的数学运算。
 * 
 * @class Calculator
 * @since 1.0.0
 * @see MathUtil
 */
class Calculator {
    /**
     * 初始化计算器。
     * 
     * @param {number} [precision=2] - 计算结果的小数位数
     */
    constructor(precision = 2) {
        this.precision = precision;
        this._memory = 0;
    }

    /**
     * 两个数相加。
     * 
     * @param {number} a - 第一个加数
     * @param {number} b - 第二个加数
     * @returns {number} 两数之和
     * 
     * @example
     * const calc = new Calculator();
     * calc.add(2, 3); // returns 5
     */
    add(a, b) {
        return parseFloat((a + b).toFixed(this.precision));
    }

    /**
     * 两个数相除。
     * 
     * @param {number} a - 被除数
     * @param {number} b - 除数
     * @returns {number} 两数之商
     * @throws {Error} 当除数为0时抛出
     * 
     * @example
     * const calc = new Calculator();
     * calc.divide(10, 2); // returns 5
     */
    divide(a, b) {
        if (b === 0) {
            throw new Error("除数不能为零");
        }
        return parseFloat((a / b).toFixed(this.precision));
    }

    /**
     * 获取当前内存中的值。
     * @type {number}
     */
    get memory() {
        return this._memory;
    }

    /**
     * 设置内存中的值。
     * @param {number} value - 要存储的值
     */
    set memory(value) {
        this._memory = value;
    }
}

/**
 * 数学工具类，提供常用的数学函数。
 * @class MathUtil
 */
class MathUtil {
    /**
     * 生成斐波那契数列。
     * 
     * @static
     * @param {number} n - 要生成的数列长度
     * @returns {number[]} 斐波那契数列
     * @throws {Error} 当n小于0时抛出
     */
    static fibonacci(n) {
        if (n < 0) {
            throw new Error("n不能为负数");
        }
        if (n === 0) return [];
        if (n === 1) return [0];
        
        const result = [0, 1];
        for (let i = 2; i < n; i++) {
            result.push(result[i-1] + result[i-2]);
        }
        return result;
    }
}

/**
 * 生成问候语。
 * 
 * @param {string} name - 要问候的人的名字
 * @param {string} [greeting="Hello"] - 问候语
 * @returns {string} 完整的问候语字符串
 */
function greet(name, greeting = "Hello") {
    return `${greeting}, ${name}!`;
}

/**
 * 异步获取数据（示例）。
 * 
 * @async
 * @param {string} url - 数据的URL地址
 * @param {number} [timeout=30] - 超时时间（秒）
 * @returns {Promise<Object>} 解析后的JSON数据
 * @throws {Error} 当请求超时时抛出
 */
async function fetchData(url, timeout = 30) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout * 1000);
    
    try {
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        return response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error("请求超时");
        }
        throw error;
    }
}

/**
 * 接口定义示例（TypeScript风格）。
 * @interface User
 */
interface User {
    /** 用户ID */
    id: number;
    /** 用户名 */
    name: string;
    /** 用户邮箱 */
    email: string;
}

/**
 * 箭头函数示例。
 * @type {(a: number, b: number) => number}
 */
const multiply = (a, b) => a * b;

module.exports = {
    Calculator,
    MathUtil,
    greet,
    fetchData,
    multiply
};
