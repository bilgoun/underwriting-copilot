export const individualJourney = {
  entity: {
    type: 'individual',
    fullName: '[REDACTED]',
    nationalIdFromHUR: '[REDACTED]',          // verified via registry
    nationalIdFromPortal: '[REDACTED]',       // portal input (glyph mismatch flagged in crossChecks)
    dob: '1978-08-10',
    maritalStatusRegistry: 'Бэлэвсэн',
    residenceAddress: '[REDACTED]',
    relationshipManager: { name: '[REDACTED]', email: '[REDACTED]', phone: '[REDACTED]' },
  },

  loanApplication: {
    source: 'portal_submission',
    submittedAt: '2025-07-04T10:00:00+08:00',
    purpose: 'Орон сууцны үлдэгдэл төлбөр',
    amountMNT: 101_000_000,
    tenorMonths: 36,
    paymentFrequency: 'monthly',
    primaryBorrower: {
      clan: '[REDACTED]', patronymic: '[REDACTED]', name: '[REDACTED]',
      nationalIdRaw: 'X378081007',
      genderDeclared: 'эмэгтэй',
      phone: '[REDACTED]', email: '[REDACTED]',
      address: '[REDACTED]',
      yearsAtAddress: 4, occupancyType: 'Бусад',
      household: {
        size: 5,
        maritalStatusDeclared: 'Гэрлэсэн', // conflicts with registry (widow) → crossChecks
        members: [
          { relation: 'Нөхөр', name: '[REDACTED]', nationalId: 'Ян 86012615', occupation: 'Хувиараа (барилга)', monthlyIncomeMNT: 7_000_000, phone: '[REDACTED]' },
          { relation: 'Хүү', name: '[REDACTED]', nationalId: 'УИК 19222822', occupation: 'Цэвэрлэгээ', monthlyIncomeMNT: 100_000 }
        ]
      },
      employment: {
        current: { employer: 'Хувиараа оёдлын үйл ажиллагаа', phone: '[REDACTED]', headcount: 1 },
        history: [
          { org: 'БҮЖГИЙН ОРДОН', title: 'ЭСГҮҮР', period: '2021–2024' },
          { org: 'Баянзүрх дүүрэг', title: 'Үйлчлэгч', period: '2024–2025' },
        ]
      },
      incomeExpense: {
        income: { salary: null, business: 10_000_000, rent: null, pension: null, other: null, total: 10_000_000 },
        coBorrowerOrHouseholdIncome: 6_000_000,
        expenses: { food: '300,000 x2', household: '200,000 x2', utilities: '60,000 x2', other: '10,000 x2', totalClaimed: 1_200_000 }
      },
      liabilities: [
        { lender: 'Хаан Банк', type: '—', outstandingMNT: 2_214_457.5, term: '2024.01–2025.10', notes: 'Тэжээгчээ алдсан тэтгэврээр төлдөг' },
        { lender: '— (лизинг)', type: 'Гар утасны лизинг', outstandingMNT: 2_816_799.67, term: 'дуусах 2026-05', monthlyPaymentMNT: 270_000 }
      ],
      assets: [
        { type: 'Орон сууц', certificateStatus: 'Гэрчилгээ гараагүй', location: '[REDACTED]', selfValueMNT: 155_000_000, pledged: false },
        { type: 'Машин', model: 'Prius 41', selfValueMNT: 30_000_000, pledged: false }
      ]
    }
  },

  intent: {
    amount: 101_000_000,
    tenorMonths: 36,
    purpose: 'housing_balance',
    paymentFrequency: 'monthly',
    narrative: 'Порталаар ирсэн хэрэглэгчийн мэдүүлгийг төрийн мэдээллийн сангийн баталгаажуулалттай тулган харуулж байна.',
    derived: {
      verifiedMonthlyIncomeMNT: 572_400,             // pension (verified)
      claimMonthlyIncomeMNT: 16_000_000,             // portal-entered (10m + 6m)
      maxPaymentCapFromVerifiedMNT: 228_960,         // 40% of verified pension
      affordableAmountFromVerifiedHintMNT: 6_000_000 // illustrative cap for demo
    },
  },

  // =========================
  // 1) Fetched from Government Databases
  // =========================
  governmentData: {
    items: [
      {
        id: 'fmt-eh-100202',
        name: 'Эд Хөрөнгөтэй Эсэх Лавлагаа-100202',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: {
          apartment: { address: '[REDACTED]', status: 'Худалдсан (2021-08-30)' },
          landHouse: { address: '[REDACTED]', landSqm: 399, houseSqm: 144, coOwners: 3 }
        }
      },
      {
        id: 'fmt-mar-100104',
        name: 'Гэрлэлт Бүртгэлтэй Тухай Лавлагаа-100104',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: { registeredOn: '2019-02-15', currentStatus: 'Бэлэвсэн' }
      },
      {
        id: 'fmt-addr-100103',
        name: 'Оршин Суугаа Хаягийн Тодорхойлолт-100103',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: { address: '[REDACTED]', asOf: '2025-07-03' }
      },
      {
        id: 'fmt-id-100101',
        name: 'Иргэний Үнэмлэхний Лавлагаа-100101',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: { nationalId: '[REDACTED]', name: '[REDACTED]', dob: '1978-08-10' }
      },
      {
        id: 'fmt-tsn',
        name: 'Төрийн Үйлчилгээний Нэгдсэн Системээр Дамжуулан Мэдээлэл Хариуцагчаас Олгох Лавлагаа, Тодорхойлолт',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: { scope: 'aggregated state snapshot', discrepancies: [] }
      },
      {
        id: 'fmt-zms',
        name: 'Зээлийн Мэдээллийн Лавлагаа',
        status: 'parsed',
        confidence: 0.99,
        parsedFields: {
          dpd30_12m: 0, npl: false,
          openFacilities: [
            { lender: 'M банк', product: 'Зээлийн шугам', outstanding: 58_900 },
            { lender: 'Нет Капитал ББСБ', product: 'Зээлийн шугам', outstanding: 499_732 },
            { lender: 'ТДБ', product: 'Хадгаламж барьцаалсан', outstanding: 300_000 },
            { lender: 'PENS', product: 'Тэтгэврийн зээл', outstanding: 1_670_851, maturesOn: '2025-10-01' },
          ],
          recentLargeLoan: { amount: 54_000_000, status: 'Төлөгдсөн', closedAt: '2024-12-16' }
        }
      },
      {
        id: 'fmt-bailiff',
        name: 'Шүүхийн Шийдвэр Гүйцэтгэх Ерөнхий Газар Шүүхийн Шийдвэрээр Бусдад Төлбөргүй Эсэх Тодорхойлолт',
        status: 'parsed',
        confidence: 1.0,
        parsedFields: { subjectNationalId: '[REDACTED]', subjectName: '[REDACTED]', result: 'Төлбөргүй' },
        note: 'Co-borrower subject; not the primary.'
      }
    ]
  },

  // =========================
  // 2) Submitted via Portal (customer-entered or files uploaded)
  // =========================
  submittedData: {
    items: [
      {
        id: 'app-1',
        name: 'Зээлийн Хүсэлт (Digital portal form)',
        status: 'ingested',
        confidence: 1.0,
        claimedFields: {
          purpose: 'Орон сууцны үлдэгдэл төлбөр',
          amountMNT: 101_000_000,
          tenorMonths: 36,
          monthlyIncomeClaimedMNT: 16_000_000,
          expensesClaimedMNT: 1_200_000,
          liabilities: [
            { lender: 'Хаан Банк', outstandingMNT: 2_214_457.5, paidFrom: 'pension' },
            { lender: 'Гар утасны лизинг', outstandingMNT: 2_816_799.67, monthly: 270_000, matures: '2026-05' }
          ],
          assets: [
            { type: 'apartment', certificate: 'not issued', location: '[REDACTED]', valueMNT: 155_000_000 },
            { type: 'vehicle', model: 'Prius 41', valueMNT: 30_000_000 }
          ]
        }
      },

      {
        id: 'inv-1',
        name: 'Бараа Материалын Үлдэгдэл (Digital portal form)',
        status: 'ingested',
        confidence: 1.0,
        claimedFields: { /* example fields kept minimal for demo */ }
      },

      {
        id: 'img-1',
        name: 'Бизнес Зурагнууд',
        status: 'verified',
        verification: {
          imageOSINT: { reverseSearch: 'not_found', duplicateCount: 0, stockMatchScore: 0.03 },
          metadata: { exifConsistent: true, timestampsConsistent: true },
          originalityScore: 0.92,
          conclusion: 'Seemed legit'
        }
      },

      {
        id: 'meta-1',
        name: 'Гэрчилгээ (Metadata / notary check)',
        status: 'verified',
        verification: {
          issuerMatch: true, serialFormatValid: true, timestampValid: true,
          conclusion: 'Seemed legit'
        }
      },

      {
        id: 'rent-1',
        name: 'Түрээсийн Гэрээ (OCR)',
        status: 'verified',
        ocr: { confidence: 0.92, parsedKeyFields: true },
        verification: { partiesMatch: true, datesCoherent: true, redFlags: [] , conclusion: 'Seemed legit' }
      },

      // ===== REPLACED single bank-1 with two concrete statements =====
      {
        id: 'bank-khan-1',
        name: 'Дансны Хуулга — ХААН БАНК (viewDMS 12)',
        status: 'parsed',
        confidence: 1.0,
        sourceFile: '/mnt/data/viewDMS (12).pdf',
        parsedFields: {
          period: '2024-01-01 — 2024-06-30',
          monthlyTotals: [
            { month: '2024-01', total_credit_mnt: 8_201_423.05, total_debit_mnt: 10_585_512.14 },
            { month: '2024-02', total_credit_mnt: 3_618_000.00, total_debit_mnt: 3_237_805.59 },
            { month: '2024-03', total_credit_mnt: 1_941_000.00, total_debit_mnt: 2_181_512.33 },
            { month: '2024-04', total_credit_mnt: 2_085_000.00, total_debit_mnt: 2_351_235.81 },
            { month: '2024-05', total_credit_mnt: 18_941_000.00, total_debit_mnt: 17_935_760.31 },
            { month: '2024-06', total_credit_mnt: 2_426_000.00, total_debit_mnt: 2_451_034.41 }
          ],
          incomeCategorization: {
            most_likely_income: {
              amount_mnt: 8_101_000.00,
              transactions: [
                { date: '2024-01-12', description: 'Tuvshinbayar2deel', amount: 280_000.00 },
                { date: '2024-01-15', description: 'EB-zaya egch deel', amount: 550_000.00 },
                { date: '2024-01-23', description: 'deel', amount: 700_000.00 },
                { date: '2024-01-23', description: 'EB -deel 6,hantaaz tovch 2', amount: 860_000.00 },
                { date: '2024-01-27', description: 'deel', amount: 3_000_000.00 },
                { date: '2024-01-27', description: 'huwtsas zaswar', amount: 15_000.00 },
                { date: '2024-02-01', description: 'EB -zaya egch deel 7', amount: 1_050_000.00 },
                { date: '2024-02-05', description: 'oki-s deelnii mongo', amount: 380_000.00 },
                { date: '2024-02-07', description: 'EB -дээл заяа эгч', amount: 660_000.00 }
              ],
              comment: '“deel/ойдол/хувцас/засвар” түлхүүр үгтэй бичил орлогууд — ихэнх нь жижиг дүнтэй, тогтмол бус.'
            },
            not_verifiable: {
              amount_mnt: 3_239_423.05,
              comment: 'Хувь хүнээс тодорхойлолтгүй шилжүүлгүүд; бизнесийн орлого эсэх нь баталгаагүй.'
            },
            most_likely_not_income: {
              amount_mnt: 26_230_000.00,
              comment: '“ЗЭЭЛ ОЛГОЛТ”, нэг удаагийн шилжүүлэг, данс хаалт, урамшуулал гэх мэт давтагддаггүй орлогууд.'
            }
          },
          patterns: [
            'Орлого улирлын шинжтэй хэлбэлзэлтэй; 2024-01 нэлээд өндөр, бусад нь бага.',
            '2024-05 сард өндөр орлого (≈₮18.94m) — эх үүсвэр нь холимог; тогтмол гэдгийг нотлох баримт хомс.'
          ]
        }
      },

      {
        id: 'bank-tdb-1',
        name: 'Дансны Хуулга — ТДБ (viewDMS 16)',
        status: 'parsed',
        confidence: 1.0,
        sourceFile: '/mnt/data/viewDMS (16).pdf',
        parsedFields: {
          period: '2025-06-01 — 2025-06-27',
          totals: { total_credit_mnt: 18_941_500.00, total_debit_mnt: 18_942_623.23, end_balance_mnt: 52_469.30 },
          incomeCategorization: {
            most_likely_income: {
              amount_mnt: 2_850_000.00,
              transactions: [
                { date: '2025-06-09', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 40_000.00 },
                { date: '2025-06-13', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 500_000.00 },
                { date: '2025-06-14', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 700_000.00 },
                { date: '2025-06-15', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 10_000.00 },
                { date: '2025-06-15', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 20_000.00 },
                { date: '2025-06-17', description: 'From:ЖАРГАЛСАЙХАН ГАНСҮХ', amount: 50_000.00 },
                { date: '2025-06-25', description: 'From:ЭНХМЭНД ЧОЙМПОГ', amount: 1_080_000.00 },
                { date: '2025-06-26', description: 'From:ЭНХМЭНД ЧОЙМПОГ', amount: 450_000.00 }
              ],
              comment: 'Нэр заасан хувь хүмүүсээс ирсэн P2P орлого — боломжит борлуулалтын орлого боловч бизнесийн гүйлгээ гэх баталгаа дутмаг.'
            },
            not_verifiable: {
              amount_mnt: 15_141_500.00,
              comment: 'Масклагдсан карт/дансны дугаартай кредитүүд (жишээ нь “36967*****76353”). Үүнд 2025-06-24-ний ₮4.0m ба ₮0.6m зэрэг багтсан — POS/QR тооцоо эсвэл дотоод шилжүүлэг байж болох ч зорилго тодорхойгүй.'
            },
            most_likely_not_income: {
              amount_mnt: 950_000.00,
              comment: '“ЗЭЭЛ ОЛГОЛТ” тэмдэглэгээтэй 9 кредит — зээлийн олголт тул орлого гэж тооцохгүй.'
            }
          },
          suspiciousPatterns: [
            {
              id: 'same_day_pass_through',
              date: '2025-06-24',
              detail: 'Нэг өдөр ₮4,624,000 орж, бараг ижил хэмжээний ₮4,623,150 зарлагадсан — “To:БАТЗАЯА БАЗАРДАРЬ / 05-Хаан Банк …” мөрүүдээр өөр данс руу дамжуулсан шинжтэй.'
            },
            {
              id: 'counterparty_roundtrip',
              detail: 'ЖАРГАЛСАЙХАН ГАНСҮХ-ээс нийт ₮1.32m орж, буцаан ₮40k гарсан — хоёр талын урсгал байгаа ч зорилго тодорхойгүй.'
            },
            {
              id: 'thin_eom_balance',
              detail: 'Сарын эцэст үлдэгдэл ердөө ₮52,469.30 — өндөр эргэлттай ч хадгалалт нимгэн.'
            }
          ],
          notes: [
            'Кредитүүдэд “ОРЛОГЫН СМС МЭДЭГДЛИЙН ШИМТГЭЛ” тайлбар олон давтагдсан нь орлогын мэдэгдлийн SMS-тэй холбоотой, орлого эсэхийг батлах үндэслэл биш.',
            'Дүн шинжилгээг зөвхөн дансны хуулгад тулгуурлав; зарим борлуулалт бэлнээр хийгдэх боломжтой тул банкны хуулгад бүртгэгдэхгүй байж болно.'
          ]
        }
      }
      // ===== end bank statements =====
    ]
  },

  // =========================
  // Cross-checks: Portal claims vs Government verification
  // =========================
  crossChecks: {
    executedAt: '2025-07-04T11:30:00+08:00',
    accuracyScore: 0.9,
    results: [
      { id: 'id_mismatch', label: 'РД нийцэл', status: 'warn', detail: '[REDACTED] (registry) vs [REDACTED] (portal input).' },
      { id: 'marital_status', label: 'Гэрлэлтийн статус', status: 'fail', detail: 'Registry=Бэлэвсэн; portal=Гэрлэсэн.' },
      {
        id: 'income_claims',
        label: 'Орлого (portal vs ND/банк)',
        status: 'unverified',
        detail:
          'Порталын мэдүүлэг ₮16m/сар (₮10m бизнес + ₮6m өрхийн) vs. баталгаатай тэтгэвэр ₮572.4k. ' +
          'ХААН (2024-01..06): орлогын хэлбэлзэл их, “deel/оёдол” түлхүүр үгтэй жижиг орлогуудтай ч 6 сар тогтмол ₮10m-ийг нотлохгүй. ' +
          'ТДБ (2025-06): gross credit ₮18.94m боловч үүнд ~₮0.95m “ЗЭЭЛ ОЛГОЛТ”, ~₮2.85m P2P нэртэй шилжүүлэг, ~₮15.14m масклагдсан эх үүсвэрүүд (2025-06-24-нд ₮4.62m нэг өдрийн дамжин өнгөрөлт) багтсан — тогтвортой бизнесийн орлого гэж батлахад дутуу. ' +
          'Иймд ₮10m/сар шаардлага хангаж буйг банкны хуулгаар дангаар батлах боломжгүй; ' +
          'борлуулалтын тодорхой хэсэг бэлнээр хийгддэг (хуулгад тусгагдаагүй) байх магадлалтай.'
      },
      { id: 'liabilities', label: 'Өрийн мэдээлэл (portal vs ЗМС)', status: 'mixed', detail: 'Portal: KhanBank/phone lease; ZMS: PENS + small lines; reconcile needed.' },
      { id: 'property_status', label: 'Барьцааны боломж', status: 'fail', detail: 'Registry flat sold; land/house co-owned; portal apartment has no certificate.' },
      { id: 'biz_photos', label: 'Бизнес зураг (OSINT + metadata)', status: 'pass', detail: 'Not found online; EXIF consistent; originality high.' },
      { id: 'rent_agreement', label: 'Түрээсийн гэрээ (OCR)', status: 'pass', detail: 'OCR conf=0.92; parties/dates coherent; no red flags.' },
      { id: 'gov_fetch_complete', label: 'Gov data fetched', status: 'pass', detail: 'All 7 government data sources ingested.' },
    ],
  },

  rules: {
    policyPrequal: {
      status: 'fail',
      executedAt: '2025-07-04T11:10:00+08:00',
      rules: [
        { id: 'income_min', status: 'fail', evidence: 'Verified recurring income ₮572,400/сар; portal-claimed ₮16m unverified.' },
        { id: 'debt_capacity', status: 'fail', evidence: 'Active PENS 1.67m + small lines; plus portal-claimed liabilities to reconcile.' },
        { id: 'credit_clean', status: 'pass', evidence: 'ЗМС DPD30=0; NPL=false.' },
        { id: 'collateral_clean', status: 'fail', evidence: 'Clean first-lien collateral not demonstrated (registry flat sold; co-owned land/house; portal apartment w/o certificate).' },
      ],
    },
    productMatch: {
      decidedAt: '2025-07-04T11:20:00+08:00',
      recommendedProducts: [
        {
          id: 'micro',
          label: '36 сарын жижиг хэмжээний зээл',
          limit: 6_000_000,
          pricingBand: '16–21% (illustrative)',
          paymentCap: 228_960,
          comments: 'PENS хаасны дараа; ADB from pension.'
        }
      ],
      rejectedProducts: [
        { id: 'housing_balance_topup', reason: 'P/I хүрэлцэхгүй (verified income basis)' },
        { id: 'large_unsecured', reason: 'P/I хүрэлцэхгүй' }
      ]
    }
  },

  loanCommittee: {
    recordedAt: '2025-07-04T11:45:00+08:00',
    moderator: 'GPT-5-Pro',
    panel: [
      { name: 'GPT-5-Pro', role: 'Senior credit · Moderator' },
      { name: 'Gemini-2.5-Pro', role: 'Bank statement analyst' },
      { name: 'Claude Opus', role: 'Cash uplift reviewer' },
      { name: 'Grok-4-Heavy', role: 'RM liaison' },
      { name: 'DeepSeek R1', role: 'Risk & affordability' }
    ],
    transcript: [
      {
        speaker: 'GPT-5-Pro',
        focus: 'Case setup & income methodology',
        content:
          'Thanks, everyone. Case: ₮101,000,000, 36 months, purpose: housing balance. Verified income is ₮572,400/mo (pension). Claimed income: ₮10,000,000/mo from tailoring business, plus ₮6,000,000/mo claimed for a co-borrower (no statements provided yet). Collateral: no clean first lien today; title on target apartment not yet issued. There are RD glyph and marital-status mismatches.\nBefore affordability, let’s agree on income methodology: we will not ignore bank inflows; we’ll subtract red-flag items (e.g., explicit loan proceeds, pass-throughs), then consider a cash uplift because this business likely has cash sales. We’ll compare the resulting range to the ₮10m claim. Then we’ll add a scenario where the co-borrower’s ₮6m is verified. Sound good?'
      },
      {
        speaker: 'Gemini-2.5-Pro',
        focus: 'Bank statement math',
        content:
          'Agreed. From the statements we have:\nKhan (Jan–Jun 2024) total credits: ≈ ₮37.21m (avg ₮6.20m/mo).\n“Most likely not income” (e.g., loan/one-offs): ₮26.23m over the 6 months → net ≈ ₮10.98m → ~₮1.83m/mo attributable.\n“Not verifiable yet”: ₮3.24m over 6 months. If we conservatively count 50%, add ~₮0.27m/mo.\nKhan banked income proxy: ~₮2.1m/mo.\nTDB (June 2025) one month: total credits ₮18.94m; “most likely income” ₮2.85m after excluding loan disbursements and obvious pass-throughs.\nTDB banked income proxy: ~₮2.85m/mo (single-month snapshot).'
      },
      {
        speaker: 'Claude Opus',
        focus: 'Cash uplift calibration',
        content:
          'Cash-based uplift: for micro-merchants we often see banking capture at 40–60%.\nIf Khan ~₮2.1m reflects 50% capture, true business income ≈ ₮4.2m/mo (at 40% capture, ~₮5.25m).\nIf TDB ~₮2.85m at 50% capture, true ≈ ₮5.7m (at 40%, ~₮7.1m).\nConclusion: on a generous but explainable uplift, borrower-only income is likely in the ₮4–7m/mo band, which is below the ₮10m claim but directionally supportive of a higher figure than raw banked numbers.'
      },
      {
        speaker: 'Grok-4-Heavy',
        focus: 'Co-borrower scenario',
        content:
          'Now co-borrower: claimed ₮6m/mo, no proofs yet. If we verify that with six months of statements/tax filings, then combined income ranges:\nLow case (borrower ₮4.2m + co-borrower ₮6m) = ₮10.2m/mo.\nUpper plausible (borrower ₮7.1m + co-borrower ₮6m) = ₮13.1m/mo.'
      },
      {
        speaker: 'DeepSeek R1',
        focus: 'Affordability math',
        content:
          'Affordability math for ₮101m/36m:\nPayment ≈ ₮3.55m @16%, ₮3.65m @18%, ₮3.81m @21%.\nIf policy cap is 40% of verified monthly income, required verified income is ~₮8.9–₮9.5m/mo.\nSo: borrower alone even with cash uplift doesn’t reach this threshold. With a verified co-borrower at ₮6m, total could exceed the threshold (≥ ₮9–9.5m), subject to documentation and stability.'
      },
      {
        speaker: 'GPT-5-Pro',
        focus: 'Risk callouts',
        content:
          'Other points: there’s an active PENS pension loan; phone lease ₮270k/mo; thin month-end balances; and KYC mismatches. Collateral is not presently lienable. We can set cure conditions.'
      },
      {
        speaker: 'Gemini-2.5-Pro',
        focus: 'Conditional approval path',
        content:
          'Proposal:\nAs-filed ₮101m → Defer / Conditional Approval Path (not an outright yes), contingent on:\nCo-borrower verification: six months of statements and/or tax filings showing ≥ ₮6m/mo stable income.\nBorrower sales substantiation: reclassify masked credits via PSP/acquirer reports, invoices, and tax returns to show a verified, recurring ≥ ₮3.5m–₮4m/mo (so combined ≥ ₮9–₮10m/mo).\nCollateral: provide clean first-lien (issued title + lien search).\nKYC cures: RD glyph normalization; marital-status reconciliation.\nLiability treatment: settle PENS pre-disbursement or include in DTI and still pass.\nIn parallel, offer a relationship micro product (≤ ₮6m/36m) anchored to pension, while they assemble proofs.'
      },
      {
        speaker: 'Claude Opus',
        focus: 'Support',
        content:
          'I support that. It respects the cash nature of the business (we’re not ignoring it), but keeps us within policy by requiring verifiable evidence to reach the ₮9–₮9.5m affordability threshold.'
      },
      {
        speaker: 'DeepSeek R1',
        focus: 'Audit requirements',
        content:
          'Add audit requirements: keep a classification memo for each re-labeled “masked” credit (attach PSP statements), and require six consecutive months continuity. Any gaps reset the clock.'
      },
      {
        speaker: 'Grok-4-Heavy',
        focus: 'Execution',
        content:
          'I’ll manage the checklist with the applicant and the co-borrower. If they can’t produce the evidence, we keep the micro only.'
      },
      {
        speaker: 'GPT-5-Pro',
        focus: 'Vote tally',
        content:
          'Let’s vote on two motions.\nVote\nAs-Filed Decision (₮101,000,000, 36m):\nMotion: Defer — Conditional Approval Path (not approved today; approvable if conditions are met).\nResult: 5 / 5 — Yes.\nBridge Offer:\nMotion: Offer Micro ≤ ₮6,000,000, 36m (APR 16–21%), auto-debit from pension, to maintain relationship during documentation phase.\nResult: 5 / 5 — Yes.'
      }
    ],
    motions: [
      {
        id: 'asFiled',
        title: 'As-filed request (₮101,000,000 · 36 сар)',
        proposal: 'Motion: Defer — Conditional Approval Path (not an outright yes; approvable if conditions are met).',
        result: '5 / 5 — Yes',
        rationale:
          'Зээлдэгчийн дангаарах орлого ₮4–₮7m/сар бүсээс цааш батлагдахгүй, бодлогын ₮9m босго хүрэхийн тулд хамтран зээлдэгчийн нотолгоо болон банк-трейс хийсэн бэлэн мөнгөний баримт зайлшгүй.',
        conditions: [
          'Хамтран зээлдэгч: 6 сарын дансны хуулга эсвэл татварын баримтаар ≥ ₮6m/сар тогтвортой орлого батлах.',
          'Зээлдэгчийн борлуулалт: PSP/acquirer тайлан, нэхэмжлэл, татварын мэдүүлгээр масклагдсан шилжүүлгийг дахин ангилж, ≥ ₮3.5–₮4m/сар давтагдах орлого нотлох.',
          'Барьцаа: зорилтот байрны гэрчилгээг авч, өрхийн хайлт хийлгэн эхний барьцааг цэвэр болгох.',
          'KYC cure: RD glyph-ийг нэг стандарт руу, гэрлэлтийн статусыг бүртгэлтэй нийцүүлэх.',
          'Өрийн эмчилгээ: PENS-г дисбурсаас өмнө хаах эсвэл DTI-д шингээгээд ч бодлогын хязгаарт багтаах.',
          'Аудит: масклагдсан шилжүүлэг бүрийн classification memo-д нотолгоо хавсаргаж, 6 сарын тасралтгүй байдлыг хадгалах.'
        ]
      },
      {
        id: 'bridge',
        title: 'Bridge / relationship offer',
        proposal: 'Motion: Offer Micro ≤ ₮6,000,000, 36 сар (APR 16–21%) auto-debited from pension.',
        result: '5 / 5 — Yes',
        rationale: 'Баталгаатай тэтгэврийн урсгалаар харилцааг хадгалж, урт хугацааны нотолгоо цуглуулах хугацаанд exposure-ийг хязгаарлана.',
        conditions: [
          'Auto-debit-ийг тэтгэврээс тогтвортой гүйцэтгэх ба дээд хэмжээ ₮6m.',
          'PENS-г дисбурсаас өмнө хаах эсвэл давхар төлөлтийн DTI нийцлийг баталгаажуулах.',
          'Grok-4-Heavy-ийн checklist-ийн бүх cure биелээгүй тохиолдолд микрогийн санал автоматаар хүчингүй болно.'
        ]
      }
    ],
    followUps: [
      'Grok-4-Heavy: зээлдэгч/хамтран зээлдэгчийн cure checklist болон баримтын урсгалыг удирдах.',
      'DeepSeek R1: масклагдсан шилжүүлгийн classification memo бүрийг аудитын мөрдөхүйц байдлаар хадгалах, 6 сарын завсар гарвал шинэчилж эхлэх.',
      'RM баг: харилцааны микрог санал болгож, нөхцлүүдийг тайлбарлан баримтын явцтай уялдуулах.'
    ]
  },

  rmPackage: {
    generatedAt: '2025-07-04T12:00:00+08:00',
    dossierPdf: '/mock/rm-package/batzayaa-credit360.pdf',
    dossierJson: '/mock/rm-package/batzayaa-credit360.json',
    summary: {
      decision: 'Decline (as-filed)',
      dscr: null,
      debtCapacity: 6_000_000,
      riskHighlights: [
        'Verified recurring income: ₮572.4k/сар (pension)',
        'Active PENS + small lines',
        'No clean first-lien collateral established'
      ],
      nextActions: [
        'Confirm RD glyph + marital-status discrepancies',
        'Provide bank-traced proof for claimed business & household incomes (≥6 months)',
        'Reconcile Khan Bank vs ZMS liabilities',
        'Provide title/certificate & lien status for the apartment to be paid off'
      ],
      counterOffer: {
        product: 'Micro 36m',
        maxAmountMNT: 6_000_000,
        conditions: [
          'Auto-debit from pension',
          'Settle PENS prior to disbursement',
          'Maintain avg EOM balance ≥ ₮500k for 3 months'
        ]
      }
    }
  },

  security: {
    rbacRoles: [
      { role: 'rm', permissions: ['view_dossier', 'comment', 'request_changes'] },
      { role: 'ops', permissions: ['rerun_collectors', 'upload_docs', 'audit_trail'] },
      { role: 'auditor', permissions: ['download_logs', 'view_hash_chain'] }
    ],
    encryption: { transit: 'mTLS 1.3', atRest: 'KMS+envelope' },
    audit: { hashChain: 'SHA3-256', lastSeal: '2025-07-04T12:00:00+08:00' }
  }
}

export default individualJourney
