/** What the API reports about itself through its liveness probe. */
export interface ServiceStatus {
  service: string;
  version: string;
  environment: string;
  status: string;
}
