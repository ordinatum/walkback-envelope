/* Проверка ИНВАРИАНТОВ модели Walkback Envelope.

   Инвариант — утверждение, которое обязано быть истинным во ВСЁМ
   пространстве состояний, а не в конкретном примере. Выборочные прогоны
   («покликали, вроде работает») пропускают целые классы ошибок: ровно так
   мимо трёх QA-прогонов прошли GO при невыполнимом плане и тревога по
   укрытию у вернувшегося астронавта.

   Запуск: вставляется в страницу, возвращает список нарушений. */
(function(){
  const M = window.__model;
  const C = M.consts();
  const V = [];                        // найденные нарушения
  const fail = (inv, ctx, detail) => V.push({inv, ctx, detail});

  const SITES = [0,1,2,3];
  const SCENS = ['nominal','storm','scrub','flare'];   // реальные ключи SCEN

  function ctxStr(p, t){
    return `site=${p.site} scen=${p.scen} havens=${p.havens?1:0} ` +
           `pace=${p.pace} mass=${p.mass} res=${p.res}` + (t!==undefined?` t=${t}`:'');
  }

  function checkRun(p){
    M.setParams(p);

    /* ИНВ-0. Заданные параметры должны реально примениться.
       Без этой проверки весь прогон может идти на одном наборе значений,
       притворяясь перебором: слайдер темпа хранит децикилометры, подача
       км/ч молча зажималась в минимум, и 288 конфигураций вырождались
       в одну. Проверка пространства, которая не проверяет само
       пространство, бесполезна. */
    {
      const s0 = M.probe(0);
      if (Math.abs(s0.actualPace - p.pace) > 0.051)
        fail('INV-0 params actually applied', ctxStr(p),
             `pace asked ${p.pace}, got ${s0.actualPace}`);
      if (Math.abs(s0.actualMass - p.mass) > 0.5)
        fail('INV-0 params actually applied', ctxStr(p),
             `mass asked ${p.mass}, got ${s0.actualMass}`);
      if (Math.abs(s0.actualRes - p.res) > 0.5)
        fail('INV-0 params actually applied', ctxStr(p),
             `reserve asked ${p.res}, got ${s0.actualRes}`);
    }

    /* ИНВ-1. Стоимость возврата ИЗ хабитата равна нулю.
       Нарушение означает, что поле стоимости и позиция базы рассогласованы. */
    const nh = M.needAtHab();
    if (nh.h > 1e-6 || nh.d > 1)
      fail('INV-1 needAt(HAB)==0', ctxStr(p), `h=${nh.h.toFixed(4)} d=${nh.d.toFixed(1)}`);

    let prev = null, prevArea = null, pnrSeen = null;
    const TS = [0,20,45,70,100,130,160,190,220,250,280,310,340,360];

    for (const t of TS){
      const s = M.probe(t);
      const cx = ctxStr(p, t);

      /* ИНВ-2. Дома — значит дома: нулевое удаление и нулевой путь назад. */
      if (s.phase === 'home' && (s.range > 1 || s.back_h > 1e-6))
        fail('INV-2 home => range==0 && back==0', cx,
             `range=${s.range.toFixed(0)}m back=${(s.back_h*60).toFixed(1)}min`);

      /* ИНВ-3. Расходники не возрастают (кроме пополнения в укрытии). */
      if (prev && !p.havens){
        for (const k of Object.keys(s.rem))
          if (s.rem[k] > prev.rem[k] + 1e-6)
            fail('INV-3 consumables non-increasing', cx,
                 `${k}: ${prev.rem[k].toFixed(3)} -> ${s.rem[k].toFixed(3)}`);
      }

      /* ИНВ-4. Доза не убывает. */
      if (prev && s.dose < prev.dose - 1e-9)
        fail('INV-4 dose non-decreasing', cx, `${prev.dose.toFixed(4)} -> ${s.dose.toFixed(4)}`);

      /* ИНВ-5. Отрицательный остаток обязан означать пробитый резерв.
         Если канал ушёл в минус, а запас выше резерва — модель противоречит
         сама себе. */
      for (const k of Object.keys(s.rem))
        if (s.rem[k] < 0 && s.margin >= s.res)
          fail('INV-5 deficit => margin<reserve', cx,
               `${k}=${s.rem[k].toFixed(3)} margin=${s.margin.toFixed(1)} res=${s.res}`);

      /* ИНВ-6. Положение астронавта внутри зоны тогда и только тогда,
         когда запас не ниже резерва. Зона и вердикт читают одно поле —
         расхождение означает, что они разошлись. */
      /* Допуск: заливка зоны считается по ЦЕНТРАМ ячеек (298 м), а margin —
         в точной позиции астронавта. У обрыва соседние центры расходятся
         на несколько пунктов, поэтому расхождения у самой границы законны.
         Нарисованная граница берётся из интерполированного поля и точна;
         грубая на одну ячейку только заливка. Ловим расхождения ВДАЛИ
         от порога — вот они означали бы, что зона и вердикт разошлись. */
      const shouldBeIn = s.margin >= s.res;
      const nearEdge = Math.abs(s.margin - s.res) <= 6;
      if (s.phase !== 'home' && shouldBeIn !== s.inZone && !nearEdge)
        fail('INV-6 position-in-zone <=> margin>=reserve', cx,
             `margin=${s.margin.toFixed(1)} res=${s.res} inZone=${s.inZone}`);

      /* ИНВ-7. PNR не зависит от положения ползунка времени: это свойство
         плана и параметров, а не текущей минуты. */
      if (pnrSeen === null) pnrSeen = s.pnr;
      else if (pnrSeen !== s.pnr)
        fail('INV-7 PNR independent of t', cx, `was ${pnrSeen}, now ${s.pnr}`);

      /* ИНВ-8. Удаление не превышает длину маршрута. */
      if (s.range > s.routeLen + C.CELL_M)
        fail('INV-8 range <= routeLen', cx,
             `range=${s.range.toFixed(0)} routeLen=${s.routeLen.toFixed(0)}`);

      /* ИНВ-9. Площадь зоны не растёт по ходу выхода (ресурсы только
         тратятся). Для укрытий не проверяем: пополнение законно. */
      if (prevArea !== null && !p.havens && s.areaCells > prevArea + 2)
        fail('INV-9 zone area non-increasing', cx, `${prevArea} -> ${s.areaCells} cells`);

      /* ИНВ-10. Время возврата согласовано с расстоянием и темпом:
         путь по рельефу не может быть быстрее прямой при том же темпе. */
      if (s.back_m > 0 && s.back_h > 0){
        const paceMs = Number(p.pace)/3.6;
        const minH = s.back_m/(paceMs*3600);
        if (s.back_h < minH*0.95)
          fail('INV-10 walkback time >= distance/pace', cx,
               `back=${(s.back_h*60).toFixed(1)}min min=${(minH*60).toFixed(1)}min`);
      }

      prev = s; prevArea = s.areaCells;
    }

    /* ИНВ-11. Невыполнимый план обязан где-то обернуться пробоем резерва,
       а выполнимый — не обязан. Проверяем согласие прогноза с исходом. */
    const s0 = M.probe(0), sEnd = M.probe(C.EVA_MAX);
    if (s0.feasible && sEnd.margin < 0)
      fail('INV-11 feasible => no deficit at end', ctxStr(p),
           `margin_end=${sEnd.margin.toFixed(1)}`);

    /* ИНВ-12. Укрытия не могут УМЕНЬШАТЬ зону: это дополнительные
       источники в том же поле. */
    if (!p.havens){
      const areaOff = M.probe(200).areaCells;
      M.setParams({...p, havens:true});
      const areaOn = M.probe(200).areaCells;
      if (areaOn < areaOff - 2)
        fail('INV-12 havens never shrink the zone', ctxStr(p),
             `off=${areaOff} on=${areaOn} cells`);
      M.setParams({...p, havens:false});
    }
  }

  /* Полный список конфигураций — порции запускаются снаружи */
  window.__invCfgs = (()=>{
    const out=[];
    for (const site of SITES)
      for (const scen of SCENS)
        for (const pace of [0.9, 1.7, 2.8])
          for (const mass of [0, 30])
            for (const res of [10, 25, 40])
              out.push({site, scen, havens:false, pace, mass, res});
    return out;
  })();

  window.__invRun = (from, to) => {
    V.length = 0;
    for (let i=from; i<Math.min(to, window.__invCfgs.length); i++) checkRun(window.__invCfgs[i]);
    return {from, to, violations:V.length, items:V.slice(0,60),
            byInv: V.reduce((a,v)=>{a[v.inv]=(a[v.inv]||0)+1; return a;},{})};
  };
  return {total: window.__invCfgs.length};
})()
