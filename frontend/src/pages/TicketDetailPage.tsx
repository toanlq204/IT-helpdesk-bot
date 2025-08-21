import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'

export const TicketDetailPage = () => {
  const { id } = useParams()

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ticket #{id}</h1>
        <p className="text-gray-600">Ticket details and history</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ticket Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500 py-8">
            Ticket details will be displayed here.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
