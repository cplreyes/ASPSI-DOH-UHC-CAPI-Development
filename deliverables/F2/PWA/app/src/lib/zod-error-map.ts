import { z } from 'zod';

const errorMap: z.ZodErrorMap = (issue, ctx) => {
  if (issue.code === z.ZodIssueCode.invalid_type && issue.expected === 'number') {
    if (issue.received === 'nan' || issue.received === 'undefined') {
      return { message: 'Please enter a number' };
    }
  }
  if (issue.code === z.ZodIssueCode.too_small && issue.type === 'number') {
    return { message: `Must be at least ${issue.minimum}` };
  }
  if (issue.code === z.ZodIssueCode.too_big && issue.type === 'number') {
    return { message: `Must be at most ${issue.maximum}` };
  }
  return { message: ctx.defaultError };
};

z.setErrorMap(errorMap);
