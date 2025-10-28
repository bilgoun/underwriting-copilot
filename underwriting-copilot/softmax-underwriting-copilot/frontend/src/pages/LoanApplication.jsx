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

const formatCurrency = (value) => `₮${value.toLocaleString('en-US')}`

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

  const totalSteps = 4

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

    if (currentStep === 2) {
      if (!form.fullName.trim()) messages.fullName = 'Нэрээ оруулна уу'
      if (!form.companyName.trim()) messages.companyName = 'Компанийн нэрээ оруулна уу'
      if (!form.email.trim()) messages.email = 'И-мэйлээ оруулна уу'
      if (!form.phone.trim()) messages.phone = 'Утасны дугаар оруулна уу'
    }

    if (currentStep === 3) {
      if (!form.fundingPurpose.trim()) {
        messages.fundingPurpose = 'Санхүүжилтийн зорилгоо тайлбарлана уу'
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

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const toggleRequirement = (id) => {
    setCheckedRequirements((prev) =>
      prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id],
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

          {step === 2 && (
            <div className="loan-application__form">
              <label className="loan-application__field">
                <span>Таны нэр</span>
                <input
                  type="text"
                  value={form.fullName}
                  onChange={(event) => handleChange('fullName', event.target.value)}
                  placeholder="Овог Нэр"
                />
                {errors.fullName && <small>{errors.fullName}</small>}
              </label>

              <label className="loan-application__field">
                <span>Компанийн нэр</span>
                <input
                  type="text"
                  value={form.companyName}
                  onChange={(event) => handleChange('companyName', event.target.value)}
                  placeholder="Компанийн бүртгэлтэй нэр"
                />
                {errors.companyName && <small>{errors.companyName}</small>}
              </label>

              <div className="loan-application__field-group">
                <label className="loan-application__field">
                  <span>И-мэйл</span>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) => handleChange('email', event.target.value)}
                    placeholder="name@email.com"
                  />
                  {errors.email && <small>{errors.email}</small>}
                </label>
                <label className="loan-application__field">
                  <span>Утас</span>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(event) => handleChange('phone', event.target.value)}
                    placeholder="+976 8000-0000"
                  />
                  {errors.phone && <small>{errors.phone}</small>}
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="loan-application__form">
              <label className="loan-application__field">
                <span>Санхүүжилт юунд зориулагдах вэ?</span>
                <textarea
                  value={form.fundingPurpose}
                  onChange={(event) => handleChange('fundingPurpose', event.target.value)}
                  placeholder="Жишээ нь: шинэ тоног төхөөрөмж авах, бараа татах гэх мэт"
                  rows={6}
                />
                {errors.fundingPurpose && <small>{errors.fundingPurpose}</small>}
              </label>
            </div>
          )}

          {step === 4 && (
            <div className="loan-application__form loan-application__form--slider">
              <span>Танд хэдийн хэмжээний зээл хэрэгтэй вэ?</span>
              <div className="loan-application__slider">
                <input
                  type="range"
                  min="10000000"
                  max="500000000"
                  step="1000000"
                  value={form.amount}
                  onChange={(event) => handleChange('amount', Number(event.target.value))}
                />
                <div className="loan-application__slider-values">
                  <span>₮10,000,000</span>
                  <strong>{formatCurrency(form.amount)}</strong>
                  <span>₮500,000,000</span>
                </div>
              </div>
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
