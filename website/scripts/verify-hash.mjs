import bcrypt from 'bcryptjs'
const h =
  '$2b$12$X9U.MfNpEckUSkUYVZdZoe5J/Gs2SeXb0maDXrq49SRFZB/9WjHfi'
console.log('admin123', bcrypt.compareSync('admin123', h))
