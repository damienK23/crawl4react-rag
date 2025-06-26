/**
 * Simple JavaScript file for testing hallucination detection
 * Mix of valid and invalid patterns
 */

// Valid imports
const axios = require('axios');
const { useState } = require('react');

// Invalid import
const { nonExistentFunction } = require('fake-package');

// Valid function
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Valid array operations
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const filtered = numbers.filter(n => n > 2);

// Invalid array method
const invalid = numbers.fakeMethod(n => n + 1);

// Valid console operations
console.log('Numbers:', numbers);
console.error('This is valid');

// Invalid console method
console.invalidMethod('This should be detected');

// Valid Object operations
const obj = { a: 1, b: 2 };
const keys = Object.keys(obj);
const values = Object.values(obj);

// Invalid Object method
Object.nonExistentMethod(obj);

// Valid Promise usage
fetch('/api/data')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));

// Invalid Promise method
Promise.fakeMethod().then(result => console.log(result));

// Valid Date operations
const now = new Date();
const timestamp = Date.now();

// Invalid Date method
const invalid_date = Date.nonExistentMethod();

// Valid localStorage
localStorage.setItem('key', 'value');
const item = localStorage.getItem('key');

// Invalid localStorage method
localStorage.fakeMethod('invalid');

// Valid setTimeout
setTimeout(() => {
  console.log('Delayed execution');
}, 1000);

// Invalid global function
invalidGlobalFunction();

// Export (valid)
module.exports = {
  calculateTotal,
  doubled,
  filtered
};