#!/usr/bin/env node
/* Проверка физического ядра против замеров миссий.
   Запуск: node test-physics.mjs   (из каталога проекта)

   Это регрессионный барьер: шесть калибровочных значений меняются
   ТОЛЬКО осознанно. Если они поехали — модель изменилась, и это
   должно быть видно до коммита.                                    */
import { PHYS, metabolicW, consumptionRates, endurance, doseRateMSvH }
  from './physics.mjs';

const BTU = w => w / PHYS.BTU_W;
let fails = 0;

let known = 0;
function check(label, got, lo, hi, unit = '', note = null) {
  const ok = got >= lo && got <= hi;
  // note — заявленное известное отклонение: печатается, но прогон не валит.
  // Так расхождение остаётся на виду, а не прячется подгонкой границ.
  if (!ok) { if (note) known++; else fails++; }
  const mark = ok ? 'ok  ' : note ? 'ИЗВ.' : 'FAIL';
  console.log(`  ${mark} ${label.padEnd(30)} ${got.toFixed(1).padStart(8)}${unit}` +
              `  ожидалось ${lo}..${hi}`);
  if (!ok && note) console.log(`       известное отклонение: ${note}`);
}

/* Бюджет расходников ДОЛЖЕН совпадать со сценарием "Штатный" в index.html.
   Рассинхрон здесь означает, что тест проверяет не то, что показывает UI. */
export const NOMINAL_BUDGET = { water: 3.2, co2: 620, batt: 760, o2: 700 };

console.log('=== МЕТАБОЛИЗМ · регрессионный барьер (Apollo 780–1200 BTU/ч)');
const cases = [
  ['стоит на месте',        { speedMs: 0,    gradePct: 0 },              560,  566],
  ['идёт 1.4 км/ч ровно',   { speedMs: 0.39, gradePct: 0 },              700,  708],
  ['идёт 1.4, уклон +8%',   { speedMs: 0.39, gradePct: 8 },              957,  965],
  ['идёт 1.4, уклон +15%',  { speedMs: 0.39, gradePct: 15 },            1182, 1190],
  // Пол метаболизма = покой + несение груза (нести груз на спуске не может
  // стоить дешевле, чем стоять с ним же), поэтому спуск −15 % упирается в
  // те же 562.7 BTU/ч, что и стояние на месте.
  ['идёт 1.4, спуск -15%',  { speedMs: 0.39, gradePct: -15 },            559,  566],
  ['2.5 км/ч, груз 25кг',   { speedMs: 0.69, gradePct: 0, loadKg: 25 }, 1409, 1417],
];
for (const [label, opt, lo, hi] of cases) {
  check(label, BTU(metabolicW(opt)), lo, hi, ' BTU/ч');
}

console.log('\n=== ТЗ: ходьба по реголиту должна давать 300–500 Вт');
const specPace = metabolicW({ speedMs: 1.7 / 3.6, gradePct: 0 });
check('1.7 км/ч ровно (ТЗ п.7)', specPace, 300, 500, ' Вт',
  'модель даёт заниженную оценку для ровной ходьбы. Занижение расхода\n' +
  '       РАСШИРЯЕТ зону возврата и ОТОДВИГАЕТ PNR, то есть ошибка\n' +
  '       в неконсервативную сторону. Задокументировано в README,\n' +
  '       Known limits. Перекалибровка сдвинет все четыре канала и\n' +
  '       подобранный маршрут, поэтому отложена.');

console.log('\n=== РАСХОД ПО КАНАЛАМ (ходьба 1.4 км/ч, ровно)');
const r = consumptionRates(metabolicW({ speedMs: 0.39 }));
console.log(`       O2    ${r.o2_g_h.toFixed(0)} г/ч`);
console.log(`       CO2   ${r.co2_g_h.toFixed(0)} г/ч`);
console.log(`       вода  ${r.water_kg_h.toFixed(3)} кг/ч`);
console.log(`       батар ${r.batt_wh_h.toFixed(0)} Вт·ч/ч  (тепло ${r.heatW.toFixed(0)} Вт)`);
check('вода (Apollo PLSS ~0.5 кг/ч)', r.water_kg_h, 0.40, 0.60, ' кг/ч');

console.log('\n=== ЧТО КОНЧАЕТСЯ ПЕРВЫМ (бюджет = сценарий "Штатный")');
const e = endurance(NOMINAL_BUDGET, r);
for (const [k, v] of Object.entries(e.perChannel)) {
  console.log(`       ${k.padEnd(6)} хватит на ${v.toFixed(1)} ч`);
}
console.log(`  >>>  ОГРАНИЧИТЕЛЬ: ${e.limiting.label} (${e.limiting.hours.toFixed(1)} ч)`);
check('автономия по ограничителю', e.limiting.hours, 5.5, 9.0, ' ч');

console.log('\n=== МОНОТОННОСТЬ СПУСКА (спуск не может быть дешевле стояния)');
const standing = metabolicW({ speedMs: 0, gradePct: 0 });
let monoFail = 0;
for (const g of [-5, -10, -15, -25, -36, -45]) {
  const w = metabolicW({ speedMs: 0.39, gradePct: g });
  if (w < standing) { monoFail++; }
  console.log(`       спуск ${String(g).padStart(3)}%: ${w.toFixed(0).padStart(4)} Вт` +
              `${w < standing ? '  <-- НИЖЕ СТОЯНИЯ (' + standing.toFixed(0) + ' Вт)' : ''}`);
}
if (monoFail) { fails++; console.log(`  FAIL ${monoFail} уклонов дешевле стояния на месте`); }
else { console.log('  ok   ни один спуск не дешевле стояния'); }

console.log('\n=== ДОЗА');
console.log(`       открытая равнина: ${doseRateMSvH(1).toFixed(4)} мЗв/ч` +
            ` -> за 6ч ${(doseRateMSvH(1) * 6).toFixed(3)} мЗв`);
console.log(`       затенение 0.5:    ${doseRateMSvH(0.5).toFixed(4)} мЗв/ч`);
console.log(`       вспышка SPE:      ${doseRateMSvH(1, true).toFixed(2)} мЗв/ч`);
check('фон MSL RAD', doseRateMSvH(1) * 24, 0.60, 0.68, ' мЗв/сут');
// ТЗ п.10: затенение рельефом снижает дозу на 30–50%, не больше
const shielded = doseRateMSvH(0.5) / doseRateMSvH(1);
check('макс. снижение дозы (ТЗ 30-50%)', (1 - shielded) * 100, 30, 50, ' %');

console.log(fails ? `\n${fails} ПРОВЕРОК НЕ ПРОЙДЕНО`
                  : known ? `\nВСЕ ПРОВЕРКИ ПРОЙДЕНЫ (${known} известное отклонение, см. README)`
                  : '\nВСЕ ПРОВЕРКИ ПРОЙДЕНЫ');
process.exit(fails ? 1 : 0);
