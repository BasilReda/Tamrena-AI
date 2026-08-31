type DisplayFood = {
  name: string;
  food_name_ar?: string | null;
};

const IGNORED_USDA_TOKENS = new Set([
  'raw',
  'dry',
  'nfs',
  'foundation',
  'prepared',
  'unsalted',
  'without skin',
  'without skin and bone',
  '0% moisture',
  'moisture',
  'with skin',
  'with bone',
  'cooked',
  'uncooked',
  'fresh',
  'whole grain',
  'old fashioned',
]);

const PREFIX_TOKENS = new Set([
  'defatted',
  'ground',
  'rolled',
  'roasted',
  'toasted',
  'baked',
  'grilled',
  'steamed',
  'crushed',
  'minced',
  'chopped',
  'powdered',
]);

const GENERIC_BASES = new Set([
  'beans',
  'bean',
  'flour',
  'sprouts',
  'seed',
  'seeds',
  'rice',
  'oats',
]);

const stripParenthetical = (value: string) => value.replace(/\s*\([^)]*\)/g, ' ');

const titleCase = (value: string) =>
  value
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');

export const formatFoodDisplayName = (food: DisplayFood, preferArabic = false): string => {
  const arabicName = typeof food.food_name_ar === 'string' ? food.food_name_ar.trim() : '';
  if (preferArabic && arabicName) {
    return arabicName;
  }

  const rawName = (food.name || '').trim();
  if (!rawName) {
    return arabicName || 'Unknown Food';
  }

  const parts = rawName
    .split(',')
    .map((part) => stripParenthetical(part).trim().toLowerCase())
    .filter(Boolean)
    .filter((part) => !IGNORED_USDA_TOKENS.has(part));

  if (parts.length === 0) {
    return arabicName || titleCase(rawName);
  }

  const [head, ...tail] = parts;
  const prefixTokens = tail.filter((token) => PREFIX_TOKENS.has(token));
  const bodyTokens = tail.filter((token) => !PREFIX_TOKENS.has(token));
  const mainParts: string[] = [];

  if (prefixTokens.length > 0) {
    mainParts.push(...prefixTokens.slice().reverse());
  }

  if (bodyTokens.length > 0 && GENERIC_BASES.has(head)) {
    mainParts.push(bodyTokens[0], head);
    mainParts.push(...bodyTokens.slice(1));
  } else {
    mainParts.push(head, ...bodyTokens);
  }

  const cleaned = mainParts.join(' ').replace(/\s+/g, ' ').trim();
  return cleaned ? titleCase(cleaned) : arabicName || titleCase(rawName);
};
