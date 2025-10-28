import { useNavigate } from 'react-router-dom'
import { loanProducts } from '../data/loanProducts'
import './CustomerPortal.css'

export default function CustomerPortal() {
  const navigate = useNavigate()

  const handleApply = (productId) => {
    navigate('/loan-application', { state: { productId } })
  }

  return (
    <div className="customer-portal">
      <div className="customer-portal__inner">
        <section className="customer-portal__grid">
          {loanProducts.map((product) => (
            <article key={product.id} className="loan-card">
              <div className="loan-card__media">
                <img className="loan-card__image" src={product.image} alt={product.title} />
                <div className="loan-card__overlay" />
                <div className="loan-card__content">
                  <h2 className="loan-card__title">{product.title}</h2>
                  <button
                    type="button"
                    className="loan-card__button"
                    onClick={() => handleApply(product.id)}
                  >
                    Apply
                  </button>
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}
