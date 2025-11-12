import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import businessLoanCatalog from '../data/business_loans_mn.json'
import { loanProducts } from '../data/loanProducts'
import './LoanApplication.css'

const createEmptyForm = () => ({
  fullName: '',
  companyName: '',
  email: '',
  phone: '',
  fundingPurpose: '',
  amount: 50000000,
})

const translateGroupLabel = (groupKey) => {
  const dictionary = {
    general: 'Ерөнхий шаардлага',
    supplier: 'Нийлүүлэгч байгууллага',
    buyer: 'Худалдан авагч',
    borrower: 'Зээл хүсэгч',
    equipment: 'Тоног төхөөрөмж',
  }
  return dictionary[groupKey] ?? groupKey
}

const loanQuestionSections = [
  {
    title: '1. Зээлийн мэдээлэл',
    fields: [
      { id: 'loan-type', label: 'Зээлийн төрөл' },
      { id: 'loan-interest', label: 'Зээлийн хүү (сарын)' },
      { id: 'loan-purpose', label: 'Зээлийн зориулалт' },
      { id: 'loan-term', label: 'Зээлийн хугацаа (сараар)' },
      { id: 'loan-amount-number', label: 'Хүсч буй зээлийн хэмжээ (тоогоор)' },
      { id: 'loan-amount-text', label: 'Хүсч буй зээлийн хэмжээ (үсгээр)' },
      {
        id: 'loan-frequency',
        label: 'Зээл төлөх давтамж',
        details: 'Сард 1 удаа, Сард 2 удаа',
      },
      {
        id: 'repayment-schedule',
        label: 'Зээлийн төлбөрийн хуваарь хэрхэн үүсгэх',
        details: 'Нийт төлбөр тэнцүү төлөлттэй, Үндсэн зээлийн тэнцүү төлөлттэй',
      },
    ],
  },
  {
    title: '2. Зээлдэгчийн үндсэн мэдээлэл',
    groups: [
      {
        id: 'primary-borrower',
        title: 'Үндсэн зээлдэгч',
        fields: [
          { id: 'primary-lineage', label: 'Ургийн овог' },
          { id: 'primary-parent-name', label: 'Эцэг эхийн нэр' },
          { id: 'primary-name', label: 'Нэр' },
          { id: 'primary-registration', label: 'Регистр / Иргэний бүртгэлийн дугаар' },
          { id: 'primary-gender', label: 'Хүйс' },
          { id: 'primary-phone', label: 'Гар утасны дугаар' },
          { id: 'primary-email', label: 'Цахим шуудан' },
          { id: 'primary-address', label: 'Оршин суугаа хаяг' },
          { id: 'primary-duration', label: 'Оршин сууж буй хугацаа (жилээр)' },
          {
            id: 'primary-ownership',
            label: 'Эзэмшлийн төрөл',
            details: 'Өмчлөгч, Түрээслэгч, Эцэг эхийн хамт, Бусад',
          },
          {
            id: 'primary-education',
            label: 'Боловсрол / мэргэжил',
            details: 'Бүрэн дунд, Бүрэн бус дунд, Дээд, Мэргэжлийн сургууль, Бусад',
          },
          { id: 'primary-school', label: 'Төгссөн сургууль' },
          { id: 'primary-major', label: 'Мэргэжил' },
        ],
      },
      {
        id: 'co-borrower',
        title: 'Хамтран зээлдэгч',
        fields: [
          { id: 'co-lineage', label: 'Ургийн овог' },
          { id: 'co-parent-name', label: 'Эцэг эхийн нэр' },
          { id: 'co-name', label: 'Нэр' },
          { id: 'co-registration', label: 'Регистр / Иргэний бүртгэлийн дугаар' },
          { id: 'co-gender', label: 'Хүйс' },
          { id: 'co-phone', label: 'Гар утасны дугаар' },
          { id: 'co-email', label: 'Цахим шуудан' },
          { id: 'co-address', label: 'Оршин суугаа хаяг' },
          { id: 'co-duration', label: 'Оршин сууж буй хугацаа (жилээр)' },
          {
            id: 'co-ownership',
            label: 'Эзэмшлийн төрөл',
            details: 'Өмчлөгч, Түрээслэгч, Эцэг эхийн хамт, Бусад',
          },
          {
            id: 'co-education',
            label: 'Боловсрол / мэргэжил',
            details: 'Бүрэн дунд, Бүрэн бус дунд, Дээд, Мэргэжлийн сургууль, Бусад',
          },
          { id: 'co-school', label: 'Төгссөн сургууль' },
          { id: 'co-major', label: 'Мэргэжил' },
        ],
      },
    ],
  },
  {
    title: '3. Гэр бүлийн байдал',
    groups: [
      {
        id: 'primary-family',
        title: 'Үндсэн зээлдэгч',
        fields: [
          { id: 'primary-family-size', label: 'Ам бүлийн тоо' },
          {
            id: 'primary-marital-status',
            label: 'Гэр бүлийн байдал',
            details: 'Гэрлэсэн, Гэрлээгүй, Бусад',
          },
          {
            id: 'primary-family-table',
            label: 'Гэр бүлийн гишүүдийн мэдээллийн хүснэгт',
            details:
              'Баганын толгой: Таны хэн болох, Овог нэр, Регистрийн дугаар, Эрхэлдэг ажил/сургууль, Сарын орлого, Утасны дугаар',
          },
        ],
      },
      {
        id: 'co-family',
        title: 'Хамтран зээлдэгч',
        fields: [
          { id: 'co-family-size', label: 'Ам бүлийн тоо' },
          {
            id: 'co-marital-status',
            label: 'Гэр бүлийн байдал',
            details: 'Гэрлэсэн, Гэрлээгүй, Бусад',
          },
          {
            id: 'co-family-table',
            label: 'Гэр бүлийн гишүүдийн мэдээллийн хүснэгт',
            details:
              'Баганын толгой: Таны хэн болох, Овог нэр, Регистрийн дугаар, Эрхэлдэг ажил/сургууль, Сарын орлого, Утасны дугаар',
          },
        ],
      },
    ],
  },
  {
    title: '4. Ажил эрхлэлтийн мэдээлэл',
    groups: [
      {
        id: 'primary-employment',
        title: 'Үндсэн зээлдэгч',
        fields: [
          { id: 'primary-employer', label: 'Одоогийн ажил олгогч байгууллагын нэр' },
          { id: 'primary-employer-phone', label: 'Утасны дугаар' },
          { id: 'primary-employer-size', label: 'Нийт ажилтны тоо' },
          { id: 'primary-additional-staff', label: 'Нийт нэмэлтээр оролцсон хүн/ажилчдын тоо' },
          {
            id: 'primary-hiring-trend',
            label: 'Сүүлийн 5 жилийн хугацаанд нэмэлтээр ажилд орсон хүний тоо',
          },
          {
            id: 'primary-employment-history',
            label: 'Хөдөлмөр эрхлэлтийн түүхийн хүснэгт',
            details: 'Байгууллагын нэр, Албан тушаал, Ажилласан хугацаа',
          },
        ],
      },
      {
        id: 'co-employment',
        title: 'Хамтран зээлдэгч',
        fields: [
          { id: 'co-employer', label: 'Одоогийн ажил олгогч байгууллагын нэр' },
          { id: 'co-employer-address', label: 'Ажил олгогч байгууллагын хаяг' },
          { id: 'co-employer-phone', label: 'Утасны дугаар' },
          { id: 'co-employer-size', label: 'Нийт ажилтны тоо' },
          { id: 'co-working-years', label: 'Нийт хөдөлмөр эрхэлсэн хугацаа (жилээр)' },
          {
            id: 'co-employment-history',
            label: 'Сүүлийн 5 жилийн хөдөлмөр эрхлэлтийн түүхийн хүснэгт',
            details: 'Байгууллагын нэр, Албан тушаал, Ажилласан хугацаа',
          },
        ],
      },
    ],
  },
  {
    title: '5. Хөрөнгө санхүүгийн мэдээлэл',
    fields: [
      {
        id: 'income-sources',
        label: 'Зээл эргүүлэн төлөх эх үүсвэр',
        details: 'Цалингийн орлого, Бизнесийн орлого, Тэтгэврийн орлого, Бусад орлого',
      },
      {
        id: 'income-table',
        label: 'Орлогын төрөл ба сарын дүнгийн хүснэгт',
        details: 'Өөрийн орлого болон хамтран зээлдэгч/өрхийн гишүүний орлогын багана',
      },
      {
        id: 'expense-table',
        label: 'Зардлын төрөл ба сарын дүнгийн хүснэгт',
        details: 'Хүнсний зардал, Ахуйн хэрэглээний зардал, Ашиглалтын зардал, Бусад',
      },
      { id: 'totals', label: 'Нийт орлого ба нийт зардлын тооцоо' },
    ],
  },
  {
    title: '6. Бусад банк, санхүүгийн байгууллагын зээл',
    fields: [
      {
        id: 'other-loans-flag',
        label: 'Бусад газарт зээлтэй эсэх',
        details: 'Сонголт: Тийм / Үгүй',
      },
      {
        id: 'other-loans-table',
        label: 'Зээлтэй байгууллагын жагсаалт',
        details: 'Банк, зээлийн төрөл, үлдэгдэл, дуусах хугацаа, сарын төлөлт',
      },
    ],
  },
  {
    title: '7. Эзэмшдэг хөрөнгийн мэдээлэл',
    fields: [
      { id: 'asset-type', label: 'Хөрөнгийн төрөл' },
      { id: 'asset-doc', label: 'Гэрчилгээ, регистр, дансны дугаар' },
      { id: 'asset-location', label: 'Байршил' },
      { id: 'asset-value', label: 'Харилцагчийн өөрийн үнэлгээ (төгрөгөөр)' },
      {
        id: 'asset-usage',
        label: 'Түрээслүүлсэн эсэх / үнэ төлбөргүй ашиглуулсан эсэх / бусад шаардах эрх',
      },
      { id: 'asset-pledge', label: 'Тус зээлд барьцаалах эсэх' },
    ],
  },
  {
    title: '8. Зээлээр санхүүжүүлэх автомашины мэдээлэл',
    description: 'Зөвхөн автомашины зээлийн үед бөглөнө.',
    fields: [
      { id: 'car-plate', label: 'Автомашины марк, улсын дугаар' },
      { id: 'car-year', label: 'Үйлдвэрлэсэн он' },
      { id: 'car-import-date', label: 'Монголд орж ирсэн огноо' },
      { id: 'car-price', label: 'Худалдан авах үнийн дүн' },
      { id: 'car-down-payment', label: 'Урьдчилгаа төлбөрийн дүн' },
    ],
  },
  {
    title: '9. Нэмэлт мэдээлэл',
    fields: [
      {
        id: 'emergency-contact',
        label: 'Тантай холбоо барьж чадахгүй тохиолдолд мэдээлэл дамжуулах хүн',
        details: 'Таны хэн болох, Овог нэр, Эрхэлдэг ажил/сургууль, Утасны дугаар',
      },
    ],
  },
  {
    title: '10. Нийгмийн хариуцлага',
    fields: [
      {
        id: 'waste-disposal',
        label: 'Ахуйн хогоо хогийн төвлөрсөн цэгт хаядаг эсэх',
        details: 'Тийм / Үгүй',
      },
      { id: 'garbage-fee', label: 'Сар бүр хогны мөнгө төлдөг эсэх', details: 'Тийм / Үгүй' },
      {
        id: 'education-duty',
        label: 'Сургуулийн насны хүүхдээ ерөнхий боловсролын сургуульд сургадаг эсэх',
        details: 'Тийм / Үгүй',
      },
      {
        id: 'social-commitment',
        label: 'Бид энэхүү хүсэлтэд өгсөн мэдээлэл үнэн зөв, бүрэн болохыг баталж байна.',
        details: 'Гар бичмэл баталгаа бичих хэсэг',
      },
    ],
  },
  {
    title: '11. Баталгаа ба тоон гарын үсэг',
    fields: [
      {
        id: 'declaration',
        label: 'Бид энэхүү хүсэлтэд өгсөн мэдээлэл үнэн зөв, бүрэн болохыг баталж байна.',
      },
      { id: 'primary-signature', label: 'Үндсэн зээлдэгчийн гарын үсэг' },
      { id: 'co-signature', label: 'Хамтран зээлдэгчийн гарын үсэг' },
      { id: 'signature-date', label: 'Огноо' },
    ],
  },
]

export default function LoanApplication() {
  const location = useLocation()
  const [form, setForm] = useState(createEmptyForm)
  const [step, setStep] = useState(1)
  const [errors, setErrors] = useState({})
  const [checkedRequirements, setCheckedRequirements] = useState([])
  const [requirementsConfirmed, setRequirementsConfirmed] = useState(false)
  const navigate = useNavigate()

  const selectedProduct = useMemo(() => {
    const productId = location.state?.productId
    if (!productId) return null
    return loanProducts.find((product) => product.id === productId) ?? null
  }, [location.state])

  const requirementGroups = useMemo(() => {
    if (!selectedProduct?.productKey) return []
    const productData =
      businessLoanCatalog.products.find((product) => product.key === selectedProduct.productKey) ?? null
    if (!productData?.requirements) return []

    return Object.entries(productData.requirements)
      .map(([groupKey, rawItems]) => {
        if (!Array.isArray(rawItems) || rawItems.length === 0) return null
        return {
          id: groupKey,
          title: translateGroupLabel(groupKey),
          items: rawItems.map((text, index) => ({
            id: `${groupKey}-${index}`,
            text,
          })),
        }
      })
      .filter(Boolean)
  }, [selectedProduct?.productKey])

  const requirementItemIds = useMemo(
    () => requirementGroups.flatMap((group) => group.items.map((item) => item.id)),
    [requirementGroups],
  )

  const requirementsComplete = useMemo(() => {
    if (requirementItemIds.length === 0) return true
    return requirementItemIds.every((id) => checkedRequirements.includes(id))
  }, [requirementItemIds, checkedRequirements])

  const questionnaireSections = loanQuestionSections
  const totalSteps = 1 + questionnaireSections.length
  const isRequirementsStep = step === 1
  const currentQuestionSectionIndex = step - 2
  const currentQuestionSection =
    !isRequirementsStep && currentQuestionSectionIndex >= 0
      ? questionnaireSections[currentQuestionSectionIndex] ?? null
      : null

  useEffect(() => {
    setStep(1)
    setForm(createEmptyForm())
    setErrors({})
    setCheckedRequirements([])
    setRequirementsConfirmed(false)
  }, [selectedProduct?.id])

  const validateStep = (currentStep) => {
    const messages = {}

    if (currentStep === 1 && requirementItemIds.length > 0) {
      const stepMessages = []
      if (!requirementsComplete) {
        stepMessages.push('Та бүх шаардлагыг шалгасан эсэхээ баталгаажуулна уу.')
      }
      if (!requirementsConfirmed) {
        stepMessages.push('Мэдээлэл үнэн зөв болохыг баталгаажуулна уу.')
      }
      if (stepMessages.length) {
        messages.requirements = stepMessages.join(' ')
      }
    }

    setErrors(messages)
    return Object.keys(messages).length === 0
  }

  const handleNext = () => {
    if (!validateStep(step)) return
    setStep((current) => Math.min(current + 1, totalSteps))
  }

  const handleBack = () => {
    setErrors({})
    setStep((current) => Math.max(current - 1, 1))
  }

  const handleSubmit = () => {
    if (!validateStep(step)) return
    if (!selectedProduct) {
      navigate('/customer-portal', { replace: true })
      return
    }

    navigate('/journey', {
      state: {
        productId: selectedProduct.id,
        productKey: selectedProduct.productKey,
        productTitle: selectedProduct.title,
        form,
        source: 'loan-application',
      },
    })
  }

  const toggleRequirement = (id) => {
    setCheckedRequirements((prev) =>
      prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id],
    )
  }

  const renderFields = (fields) => {
    if (!fields?.length) return null
    return (
      <ul className="loan-application__question-list">
        {fields.map((field) => (
          <li key={field.id} className="loan-application__question-item">
            <strong>{field.label}</strong>
            {field.details && <p>{field.details}</p>}
            {field.subFields && (
              <ul className="loan-application__question-sublist">
                {field.subFields.map((subField, index) => (
                  <li key={`${field.id}-${index}`}>{subField}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="loan-application__shell">
      <div className="loan-application">
        <div className="loan-application__card">
          <div className="loan-application__header">
            <div>
              <h1 className="loan-application__title">Зээлийн хүсэлт</h1>
              {selectedProduct ? (
                <p className="loan-application__subtitle">
                  {selectedProduct.title} бүтээгдэхүүний шаардлага болон мэдээлэл
                </p>
              ) : (
                <p className="loan-application__subtitle">
                  Зээлийн зөвлөхтэй холбогдохын тулд өөрийн мэдээллийг бөглөнө үү.
                </p>
              )}
            </div>
            <div className="loan-application__steps">
              {Array.from({ length: totalSteps }).map((_, index) => {
                const indicator = index + 1
                return (
                  <span
                    key={indicator}
                    className={`loan-application__step ${
                      indicator === step ? 'loan-application__step--active' : ''
                    }`}
                  />
                )
              })}
            </div>
          </div>

          {step === 1 && (
            <div className="loan-application__requirements">
              {requirementGroups.length === 0 && (
                <p className="loan-application__subtitle">
                  Энэ бүтээгдэхүүнд урьдчилсан шаардлагын жагсаалт байхгүй байна.
                </p>
              )}

              {requirementGroups.map((group) => (
                <div key={group.id} className="loan-application__requirements-group">
                  <h2 className="loan-application__requirements-title">{group.title}</h2>
                  <ul className="loan-application__requirements-list">
                    {group.items.map((item) => (
                      <li key={item.id} className="loan-application__checkbox">
                        <label>
                          <input
                            type="checkbox"
                            checked={checkedRequirements.includes(item.id)}
                            onChange={() => toggleRequirement(item.id)}
                          />
                          <span>{item.text}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              {requirementItemIds.length > 0 && (
                <label className="loan-application__confirm">
                  <input
                    type="checkbox"
                    checked={requirementsConfirmed}
                    onChange={(event) => setRequirementsConfirmed(event.target.checked)}
                  />
                  <span>Дээрх шаардлагыг хангаж байгаагаа баталгаажуулж байна.</span>
                </label>
              )}

              {errors.requirements && (
                <small className="loan-application__error">{errors.requirements}</small>
              )}
            </div>
          )}

          {!isRequirementsStep && currentQuestionSection && (
            <div className="loan-application__questionnaire">
              <div className="loan-application__step-counter">
                Алхам {Math.max(step - 1, 1)} / {Math.max(totalSteps - 1, 1)}
              </div>
              <section key={currentQuestionSection.title} className="loan-application__question-section">
                <div className="loan-application__question-section-header">
                  <h2>{currentQuestionSection.title}</h2>
                  {currentQuestionSection.description && <p>{currentQuestionSection.description}</p>}
                </div>
                {renderFields(currentQuestionSection.fields)}
                {currentQuestionSection.groups?.map((group) => (
                  <div key={group.id} className="loan-application__question-group">
                    <h3>{group.title}</h3>
                    {renderFields(group.fields)}
                  </div>
                ))}
              </section>
            </div>
          )}

          <div className="loan-application__footer">
            {step > 1 ? (
              <button type="button" className="loan-application__button" onClick={handleBack}>
                Буцах
              </button>
            ) : (
              <span />
            )}

            {step < totalSteps ? (
              <button
                type="button"
                className="loan-application__button loan-application__button--primary"
                onClick={handleNext}
              >
                Дараагийн алхам
              </button>
            ) : (
              <button
                type="button"
                className="loan-application__button loan-application__button--primary"
                onClick={handleSubmit}
              >
                Хүсэлт илгээх
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
