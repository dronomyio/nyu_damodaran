%%cuda
#include <stdio.h>
#include <math.h>

// Constants for numerical approximation of cumulative normal distribution
#define A1 0.31938153
#define A2 -0.356563782
#define A3 1.781477937
#define A4 -1.821255978
#define A5 1.330274429
#define RSQRT2PI 0.39894228040143267793994605993438

// Function to calculate cumulative normal distribution
__device__ double cnd(double x) {
    double L = fabs(x);
    double k = 1.0 / (1.0 + 0.2316419 * L);
    double w = RSQRT2PI * exp(-L * L / 2.0);
    double y = w * (A1 * k + A2 * k * k + A3 * pow(k, 3) + A4 * pow(k, 4) + A5 * pow(k, 5));
    
    return x < 0.0 ? 1.0 - y : y;
}

// CUDA kernel for warrant pricing
__global__ void warrant_pricing_kernel(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    int num_warrants,
    int num_shares,
    double* result
) {
    // Calculate dilution factor
    double dilution_factor = (double)num_shares / (num_shares + num_warrants);
    
    // Adjust stock price for dilution
    double adjusted_S = S * dilution_factor;
    
    // Strike price remains the same (no adjustment needed)
    double adjusted_K = K;
    
    // Calculate variance
    double variance = sigma * sigma;
    
    // Dividend adjusted interest rate
    double div_adj_rate = r - dividend_yield;
    
    // Calculate d1 and d2
    double d1, d2, warrant_value;
    
    if (sigma <= 0.0 || T <= 0.0) {
        warrant_value = fmax(0.0, adjusted_S - adjusted_K * exp(-r * T));
    } else {
        d1 = (log(adjusted_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * T) / (sigma * sqrt(T));
        d2 = d1 - sigma * sqrt(T);
        
        // Calculate N(d1) and N(d2) - cumulative normal distribution
        double Nd1 = cnd(d1);
        double Nd2 = cnd(d2);
        
        // Calculate warrant value using Black-Scholes formula with dilution adjustment
        warrant_value = adjusted_S * exp(-dividend_yield * T) * Nd1 - 
                        adjusted_K * exp(-r * T) * Nd2;
    }
    
    // Store the result
    *result = warrant_value;
}

// CUDA kernel for calculating Greeks
__global__ void warrant_greeks_kernel(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    int num_warrants,
    int num_shares,
    double h,
    double* greeks
) {
    // Calculate dilution factor
    double dilution_factor = (double)num_shares / (num_shares + num_warrants);
    
    // Base case
    double adjusted_S = S * dilution_factor;
    double adjusted_K = K;
    double variance = sigma * sigma;
    double div_adj_rate = r - dividend_yield;
    
    // Calculate d1 and d2 for base case
    double d1, d2, price;
    
    if (sigma <= 0.0 || T <= 0.0) {
        price = fmax(0.0, adjusted_S - adjusted_K * exp(-r * T));
    } else {
        d1 = (log(adjusted_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * T) / (sigma * sqrt(T));
        d2 = d1 - sigma * sqrt(T);
        
        double Nd1 = cnd(d1);
        double Nd2 = cnd(d2);
        
        price = adjusted_S * exp(-dividend_yield * T) * Nd1 - 
                adjusted_K * exp(-r * T) * Nd2;
    }
    
    // Calculate delta (S + h)
    double delta_S = S + h;
    double adjusted_delta_S = delta_S * dilution_factor;
    double delta_price;
    
    if (sigma <= 0.0 || T <= 0.0) {
        delta_price = fmax(0.0, adjusted_delta_S - adjusted_K * exp(-r * T));
    } else {
        double delta_d1 = (log(adjusted_delta_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * T) / (sigma * sqrt(T));
        double delta_d2 = delta_d1 - sigma * sqrt(T);
        
        double delta_Nd1 = cnd(delta_d1);
        double delta_Nd2 = cnd(delta_d2);
        
        delta_price = adjusted_delta_S * exp(-dividend_yield * T) * delta_Nd1 - 
                      adjusted_K * exp(-r * T) * delta_Nd2;
    }
    
    // Calculate delta (S - h) for gamma
    double gamma_S = S - h;
    double adjusted_gamma_S = gamma_S * dilution_factor;
    double gamma_price;
    
    if (sigma <= 0.0 || T <= 0.0) {
        gamma_price = fmax(0.0, adjusted_gamma_S - adjusted_K * exp(-r * T));
    } else {
        double gamma_d1 = (log(adjusted_gamma_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * T) / (sigma * sqrt(T));
        double gamma_d2 = gamma_d1 - sigma * sqrt(T));
        
        double gamma_Nd1 = cnd(gamma_d1);
        double gamma_Nd2 = cnd(gamma_d2);
        
        gamma_price = adjusted_gamma_S * exp(-dividend_yield * T) * gamma_Nd1 - 
                      adjusted_K * exp(-r * T) * gamma_Nd2;
    }
    
    // Calculate theta (T - h/365)
    double theta_T = T - h/365.0;
    double theta_price;
    
    if (sigma <= 0.0 || theta_T <= 0.0) {
        theta_price = fmax(0.0, adjusted_S - adjusted_K * exp(-r * theta_T));
    } else {
        double theta_d1 = (log(adjusted_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * theta_T) / (sigma * sqrt(theta_T));
        double theta_d2 = theta_d1 - sigma * sqrt(theta_T);
        
        double theta_Nd1 = cnd(theta_d1);
        double theta_Nd2 = cnd(theta_d2);
        
        theta_price = adjusted_S * exp(-dividend_yield * theta_T) * theta_Nd1 - 
                      adjusted_K * exp(-r * theta_T) * theta_Nd2;
    }
    
    // Calculate vega (sigma + h)
    double vega_sigma = sigma + h;
    double vega_variance = vega_sigma * vega_sigma;
    double vega_price;
    
    if (vega_sigma <= 0.0 || T <= 0.0) {
        vega_price = fmax(0.0, adjusted_S - adjusted_K * exp(-r * T));
    } else {
        double vega_d1 = (log(adjusted_S / adjusted_K) + (div_adj_rate + 0.5 * vega_variance) * T) / (vega_sigma * sqrt(T));
        double vega_d2 = vega_d1 - vega_sigma * sqrt(T);
        
        double vega_Nd1 = cnd(vega_d1);
        double vega_Nd2 = cnd(vega_d2);
        
        vega_price = adjusted_S * exp(-dividend_yield * T) * vega_Nd1 - 
                     adjusted_K * exp(-r * T) * vega_Nd2;
    }
    
    // Calculate rho (r + h)
    double rho_r = r + h;
    double rho_div_adj_rate = rho_r - dividend_yield;
    double rho_price;
    
    if (sigma <= 0.0 || T <= 0.0) {
        rho_price = fmax(0.0, adjusted_S - adjusted_K * exp(-rho_r * T));
    } else {
        double rho_d1 = (log(adjusted_S / adjusted_K) + (rho_div_adj_rate + 0.5 * variance) * T) / (sigma * sqrt(T));
        double rho_d2 = rho_d1 - sigma * sqrt(T);
        
        double rho_Nd1 = cnd(rho_d1);
        double rho_Nd2 = cnd(rho_d2);
        
        rho_price = adjusted_S * exp(-dividend_yield * T) * rho_Nd1 - 
                    adjusted_K * exp(-rho_r * T) * rho_Nd2;
    }
    
    // Calculate and store the Greeks
    greeks[0] = (delta_price - price) / h;                        // Delta
    greeks[1] = (delta_price - 2.0 * price + gamma_price) / (h*h); // Gamma
    greeks[2] = (theta_price - price) / (h/365.0);                // Theta
    greeks[3] = (vega_price - price) / h;                         // Vega
    greeks[4] = (rho_price - price) / h;                          // Rho
}

// Host function to calculate warrant price
extern "C" double warrant_pricing_cuda(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    int num_warrants,
    int num_shares
) {
    double h_result = 0.0;
    double *d_result;
    
    // Allocate device memory for the result
    cudaMalloc((void**)&d_result, sizeof(double));
    cudaMemset(d_result, 0, sizeof(double));
    
    // Launch the kernel
    warrant_pricing_kernel<<<1, 1>>>(
        S, K, T, r, sigma, dividend_yield, num_warrants, num_shares, d_result
    );
    
    // Copy the result back to host
    cudaMemcpy(&h_result, d_result, sizeof(double), cudaMemcpyDeviceToHost);
    
    // Free device memory
    cudaFree(d_result);
    
    return h_result;
}

// Host function to calculate warrant Greeks
extern "C" void warrant_greeks_cuda(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    int num_warrants,
    int num_shares,
    double* h_greeks
) {
    double *d_greeks;
    double h = 0.01; // Small change for finite difference
    
    // Allocate device memory for the Greeks
    cudaMalloc((void**)&d_greeks, 5 * sizeof(double));
    cudaMemset(d_greeks, 0, 5 * sizeof(double));
    
    // Launch the kernel
    warrant_greeks_kernel<<<1, 1>>>(
        S, K, T, r, sigma, dividend_yield, num_warrants, num_shares, h, d_greeks
    );
    
    // Copy the results back to host
    cudaMemcpy(h_greeks, d_greeks, 5 * sizeof(double), cudaMemcpyDeviceToHost);
    
    // Free device memory
    cudaFree(d_greeks);
}

// Main function for testing
int main() {
    // Example parameters from the Excel file
    double S = 10.0;             // Current stock price
    double K = 10.0;             // Strike price
    double T = 5.0;              // Time to expiration in years
    double sigma = 0.4;          // Volatility
    double dividend_yield = 0.0; // Dividend yield
    double r = 0.02;             // Risk-free rate
    int num_warrants = 100;      // Number of warrants outstanding
    int num_shares = 1000;       // Number of shares outstanding
    
    // Calculate warrant price
    double price = warrant_pricing_cuda(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares);
    printf("Warrant Price: %.6f\n", price);
    
    // Calculate Greeks
    double h_greeks[5];
    warrant_greeks_cuda(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares, h_greeks);
    
    printf("\nGreeks:\n");
    printf("Delta: %.6f\n", h_greeks[0]);
    printf("Gamma: %.6f\n", h_greeks[1]);
    printf("Theta: %.6f\n", h_greeks[2]);
    printf("Vega: %.6f\n", h_greeks[3]);
    printf("Rho: %.6f\n", h_greeks[4]);
    
    // Performance test
    clock_t start = clock();
    int n_iterations = 10000;
    
    for (int i = 0; i < n_iterations; i++) {
        warrant_pricing_cuda(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares);
    }
    
    clock_t end = clock();
    double execution_time = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("\nPerformance:\n");
    printf("CUDA execution time for %d iterations: %.4f seconds\n", n_iterations, execution_time);
    printf("Average time per calculation: %.4f ms\n", execution_time/n_iterations*1000);
    
    return 0;
}
