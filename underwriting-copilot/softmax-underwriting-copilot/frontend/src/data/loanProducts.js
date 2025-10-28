import businessLoanImg from '../assets/business.jpg'
import posLoanImg from '../assets/pos.jpg'
import smeLoanImg from '../assets/sme.jpg'
import supplyLoanImg from '../assets/supply.png'
import entrepreneurLoanImg from '../assets/woman_entrepreneur.jpg'

export const loanProducts = [
  {
    id: 'business',
    title: 'Бизнесийн зээл',
    image: businessLoanImg,
    productKey: 'business_loan',
  },
  {
    id: 'micro-business',
    title: 'Бичил бизнес эрхлэгчийн зээл',
    image: smeLoanImg,
    productKey: 'micro_business_loan',
  },
  {
    id: 'pos-income',
    title: 'ПОС-ын орлого барьцаалсан зээл',
    image: posLoanImg,
    productKey: 'pos_revenue_secured_loan',
  },
  {
    id: 'women-entrepreneur',
    title: 'Эмэгтэй бизнес эрхлэгчдийг дэмжих зээл',
    image: entrepreneurLoanImg,
    productKey: 'women_entrepreneur_loan',
  },
  {
    id: 'supply-chain',
    title: 'Нийлүүлэлтийн сүлжээний зээлийн эрх',
    image: supplyLoanImg,
    productKey: 'supply_chain_credit_line',
  },
]
