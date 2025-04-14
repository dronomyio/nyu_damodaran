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

// CUDA kernel for long-term option pricing
__global__ void long_term_option_pricing_kernel(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    double* results
) {
    // Calculate variance
    double variance = sigma * sigma;
    
    // Calculate d1 and d2
    double d1, d2, call_price, put_price;
    
    if (sigma <= 0.0 || T <= 0.0) {
        call_price = fmax(0.0, S - K * exp(-r * T));
        put_price = fmax(0.0, K * exp(-r * T) - S);
        d1 = 0.0;
        d2 = 0.0;
        results[0] = call_price;
        results[1] = put_price;
        results[2] = d1;
        results[3] = d2;
        results[4] = 0.0;  // N(d1)
        results[5] = 0.0;  // N(d2)
        return;
    }
    
    d1 = (log(S / K) + (r - dividend_yield + 0.5 * variance) * T) / (sigma * sqrt(T));
    d2 = d1 - sigma * sqrt(T);
    
    // Calculate N(d1) and N(d2) - cumulative normal distribution
    double Nd1 = cnd(d1);
    double Nd2 = cnd(d2);
    
    // Calculate option values using Black-Scholes formula with dividend adjustment
    call_price = S * exp(-dividend_yield * T) * Nd1 - K * exp(-r * T) * Nd2;
    
    // Put price using put-call parity
    put_price = call_price + K * exp(-r * T) - S * exp(-dividend_yield * T);
    
    // Store results
    results[0] = call_price;
    results[1] = put_price;
    results[2] = d1;
    results[3] = d2;
    results[4] = Nd1;
    results[5] = Nd2;
}

// CUDA kernel for calculating Greeks
__global__ void calculate_greeks_kernel(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    double h,
    double* greeks
) {
    // Base case
    double results[6];
    double results_up[6];
    double results_down[6];
    double results_time[6];
    double results_vol[6];
    double results_rate[6];
    
    // Base price calculation
    long_term_option_pricing_kernel<<<1, 1>>>(S, K, T, r, sigma, dividend_yield, results);
    cudaDeviceSynchronize();
    
    // Delta and Gamma calculations (S + h)
    long_term_option_pricing_kernel<<<1, 1>>>(S + h, K, T, r, sigma, dividend_yield, results_up);
    cudaDeviceSynchronize();
    
    // Gamma calculation (S - h)
    long_term_option_pricing_kernel<<<1, 1>>>(S - h, K, T, r, sigma, dividend_yield, results_down);
    cudaDeviceSynchronize();
    
    // Theta calculation (T - h/365)
    if (T <= h/365.0) {
        for (int i = 0; i < 6; i++) {
            results_time[i] = 0.0;
        }
    } else {
        long_term_option_pricing_kernel<<<1, 1>>>(S, K, T - h/365.0, r, sigma, dividend_yield, results_time);
        cudaDeviceSynchronize();
    }
    
    // Vega calculation (sigma + h)
    long_term_option_pricing_kernel<<<1, 1>>>(S, K, T, r, sigma + h, dividend_yield, results_vol);
    cudaDeviceSynchronize();
    
    // Rho calculation (r + h)
    long_term_option_pricing_kernel<<<1, 1>>>(S, K, T, r + h, sigma, dividend_yield, results_rate);
    cudaDeviceSynchronize();
    
    // Calculate Greeks
    greeks[0] = (results_up[0] - results[0]) / h;                        // Delta
    greeks[1] = (results_up[0] - 2.0 * results[0] + results_down[0]) / (h*h); // Gamma
    greeks[2] = (results_time[0] - results[0]) / (h/365.0);              // Theta
    greeks[3] = (results_vol[0] - results[0]) / h;                       // Vega
    greeks[4] = (results_rate[0] - results[0]) / h;                      // Rho
}

// Host function to calculate option price
extern "C" void long_term_option_pricing_cuda(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    double* h_results
) {
    double *d_results;
    
    // Allocate device memory for the results
    cudaMalloc((void**)&d_results, 6 * sizeof(double));
    cudaMemset(d_results, 0, 6 * sizeof(double));
    
    // Launch the kernel
    long_term_option_pricing_kernel<<<1, 1>>>(
        S, K, T, r, sigma, dividend_yield, d_results
    );
    
    // Copy the results back to host
    cudaMemcpy(h_results, d_results, 6 * sizeof(double), cudaMemcpyDeviceToHost);
    
    // Free device memory
    cudaFree(d_results);
}

// Host function to calculate Greeks
extern "C" void calculate_greeks_cuda(
    double S,
    double K,
    double T,
    double r,
    double sigma,
    double dividend_yield,
    double* h_greeks
) {
    double *d_greeks;
    double h = 0.01; // Small change for finite difference
    
    // Allocate device memory for the Greeks
    cudaMalloc((void**)&d_greeks, 5 * sizeof(double));
    cudaMemset(d_greeks, 0, 5 * sizeof(double));
    
    // Launch the kernel
    calculate_greeks_kernel<<<1, 1>>>(
        S, K, T, r, sigma, dividend_yield, h, d_greeks
    );
    
    // Copy the results back to host
    cudaMemcpy(h_greeks, d_greeks, 5 * sizeof(double), cudaMemcpyDeviceToHost);
    
    // Free device memory
    cudaFree(d_greeks);
}

// Batch pricing kernel for multiple options
__global__ void batch_option_pricing_kernel(
    double* stock_prices,
    double* strike_prices,
    double* expiration_times,
    double risk_free_rate,
    double volatility,
    double dividend_yield,
    double* call_prices,
    double* put_prices,
    int num_options
) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid < num_options) {
        double S = stock_prices[tid];
        double K = strike_prices[tid];
        double T = expiration_times[tid];
        double variance = volatility * volatility;
        
        double d1, d2, call_price, put_price;
        
        if (volatility <= 0.0 || T <= 0.0) {
            call_price = fmax(0.0, S - K * exp(-risk_free_rate * T));
            put_price = fmax(0.0, K * exp(-risk_free_rate * T) - S);
        } else {
            d1 = (log(S / K) + (risk_free_rate - dividend_yield + 0.5 * variance) * T) / (volatility * sqrt(T));
            d2 = d1 - volatility * sqrt(T);
            
            double Nd1 = cnd(d1);
            double Nd2 = cnd(d2);
            
            call_price = S * exp(-dividend_yield * T) * Nd1 - K * exp(-risk_free_rate * T) * Nd2;
            put_price = call_price + K * exp(-risk_free_rate * T) - S * exp(-dividend_yield * T);
        }
        
        call_prices[tid] = call_price;
        put_prices[tid] = put_price;
    }
}

// Host function for batch pricing
extern "C" void batch_option_pricing_cuda(
    double* h_stock_prices,
    double* h_strike_prices,
    double* h_expiration_times,
    double risk_free_rate,
    double volatility,
    double dividend_yield,
    double* h_call_prices,
    double* h_put_prices,
    int num_options
) {
    double *d_stock_prices, *d_strike_prices, *d_expiration_times;
    double *d_call_prices, *d_put_prices;
    
    // Allocate device memory
    cudaMalloc((void**)&d_stock_prices, num_options * sizeof(double));
    cudaMalloc((void**)&d_strike_prices, num_options * sizeof(double));
    cudaMalloc((void**)&d_expiration_times, num_options * sizeof(double));
    cudaMalloc((void**)&d_call_prices, num_options * sizeof(double));
    cudaMalloc((void**)&d_put_prices, num_options * sizeof(double));
    
    // Copy input data to device
    cudaMemcpy(d_stock_prices, h_stock_prices, num_options * sizeof(double), cudaMemcpyHostToDevice);
    cudaMemcpy(d_strike_prices, h_strike_prices, num_options * sizeof(double), cudaMemcpyHostToDevice);
    cudaMemcpy(d_expiration_times, h_expiration_times, num_options * sizeof(double), cudaMemcpyHostToDevice);
    
    // Calculate block and grid dimensions
    int threadsPerBlock = 256;
    int blocksPerGrid = (num_options + threadsPerBlock - 1) / threadsPerBlock;
    
    // Launch the kernel
    batch_option_pricing_kernel<<<blocksPerGrid, threadsPerBlock>>>(
        d_stock_prices, d_strike_prices, d_expiration_times,
        risk_free_rate, volatility, dividend_yield,
        d_call_prices, d_put_prices, num_options
    );
    
    // Copy results back to host
    cudaMemcpy(h_call_prices, d_call_prices, num_options * sizeof(double), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_put_prices, d_put_prices, num_options * sizeof(double), cudaMemcpyDeviceToHost);
    
    // Free device memory
    cudaFree(d_stock_prices);
    cudaFree(d_strike_prices);
    cudaFree(d_expiration_times);
    cudaFree(d_call_prices);
    cudaFree(d_put_prices);
}

// Main function for testing
int main() {
    // Example parameters from the Excel file
    double S = 500.0;             // Stock price
    double K = 600.0;             // Strike price
    double T = 15.0;              // Time to expiration in years
    double r = 0.05;              // Risk-free rate
    double sigma = sqrt(0.25);    // Volatility (sqrt of variance)
    double dividend_yield = 0.0;  // Dividend yield
    
    // Arrays to store results
    double h_results[6];  // [call_price, put_price, d1, d2, N(d1), N(d2)]
    double h_greeks[5];   // [delta, gamma, theta, vega, rho]
    
    // Calculate option prices
    long_term_option_pricing_cuda(S, K, T, r, sigma, dividend_yield, h_results);
    
    printf("Long-Term Option Pricing Results (CUDA):\n");
    printf("Stock Price: %.1f\n", S);
    printf("Strike Price: %.1f\n", K);
    printf("Time to Expiration: %.1f years\n", T);
    printf("Risk-free Rate: %.2f\n", r);
    printf("Volatility: %.6f\n", sigma);
    printf("Dividend Yield: %.1f\n", dividend_yield);
    printf("\nCalculated Values:\n");
    printf("d1: %.6f\n", h_results[2]);
    printf("N(d1): %.6f\n", h_results[4]);
    printf("d2: %.6f\n", h_results[3]);
    printf("N(d2): %.6f\n", h_results[5]);
    printf("Call Option Value: %.6f\n", h_results[0]);
    printf("Put Option Value: %.6f\n", h_results[1]);
    
    // Calculate Greeks
    calculate_greeks_cuda(S, K, T, r, sigma, dividend_yield, h_greeks);
    
    printf("\nGreeks:\n");
    printf("Delta: %.6f\n", h_greeks[0]);
    printf("Gamma: %.6f\n", h_greeks[1]);
    printf("Theta: %.6f\n", h_greeks[2]);
    printf("Vega: %.6f\n", h_greeks[3]);
    printf("Rho: %.6f\n", h_greeks[4]);
    
    // Batch pricing test
    int num_options = 1000000;
    double *h_stock_prices = (double*)malloc(num_options * sizeof(double));
    double *h_strike_prices = (double*)malloc(num_options * sizeof(double));
    double *h_expiration_times = (double*)malloc(num_options * sizeof(double));
    double *h_call_prices = (double*)malloc(num_options * sizeof(double));
    double *h_put_prices = (double*)malloc(num_options * sizeof(double));
    
    // Initialize test data
    for (int i = 0; i < num_options; i++) {
        h_stock_prices[i] = S * (0.8 + 0.4 * (double)i / num_options);
        h_strike_prices[i] = K;
        h_expiration_times[i] = T;
    }
    
    // Measure batch pricing performance
    clock_t start = clock();
    batch_option_pricing_cuda(
        h_stock_prices, h_strike_prices, h_expiration_times,
        r, sigma, dividend_yield,
        h_call_prices, h_put_prices, num_options
    );
    clock_t end = clock();
    
    double execution_time = (double)(end - start) / CLOCKS_PER_SEC;
    printf("\nBatch Pricing Performance:\n");
    printf("CUDA execution time for %d options: %.4f seconds\n", num_options, execution_time);
    printf("Average time per option: %.6f ms\n", execution_time * 1000 / num_options);
    
    // Free host memory
    free(h_stock_prices);
    free(h_strike_prices);
    free(h_expiration_times);
    free(h_call_prices);
    free(h_put_prices);
    
    return 0;
}
