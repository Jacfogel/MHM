/* International phone input shared by SMS and WhatsApp enrollment. */
window.MHMPhoneInput = {
  normalize(value) {
    if (typeof value !== 'string') return null;
    let number = value.trim().replace(/[\s().-]/g, '');
    if (number.startsWith('00')) number = '+' + number.slice(2);
    return /^\+[1-9][0-9]{7,14}$/.test(number) ? number : null;
  },
  validate(input) {
    const number = this.normalize(input.value);
    if (!number) throw new Error('Enter a mobile number with its country code, such as +1 306 555 0123. Use digits, spaces, parentheses, or hyphens; extensions are not supported.');
    input.value = number;
    return number;
  },
};
