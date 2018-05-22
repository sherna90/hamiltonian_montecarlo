#include "logistic_regression.hpp"

LogisticRegression::LogisticRegression(){
	this->normalization= false;
	this->standardization=false;
	this->with_bias = false;
}

void LogisticRegression::init(bool _normalization, bool _standardization,bool _with_bias){
	this->normalization=_normalization;
	this->standardization=_standardization;
	this->with_bias = _with_bias;
}

void LogisticRegression::init(MatrixXd &_X,VectorXd &_Y,double _lambda, bool _normalization,bool _standardization,bool _with_bias){
	bool initialized = true;
	this->with_bias = _with_bias;
	srand((unsigned int) time(0));
	this->normalization=_normalization;
	this->standardization=_standardization;
	this->lambda=_lambda;
 	this->X_train = &_X;
 	this->Y_train = &_Y;
 	tools.dataPermutation(*this->X_train,*this->Y_train);
 	if(this->normalization) tools.dataNormalization(*this->X_train,this->featureMax,this->featureMin);
 	if(this->standardization) tools.dataStandardization(*this->X_train,this->featureMean,this->featureStd);
 	if (this->with_bias) this->bias=1.0;
 	else this->bias=0.0;
 	this->rows = this->X_train->rows();
	this->dim = this->X_train->cols();
	this->weights = VectorXd::Random(dim);
	this->eta = VectorXd::Zero(this->rows);
	this->phi = VectorXd::Zero(this->rows);;
	this->grad_bias = 0.0;
	this->train_mask = VectorXd::Ones(this->dim);
	this->test_mask = VectorXd::Ones(this->dim);
 }

VectorXd LogisticRegression::sigmoid(VectorXd &eta){
	
	VectorXd phi =eta.unaryExpr([](double elem) 
	{
		double eps= numeric_limits<double>::epsilon();
	    double p= (elem>0) ? 1.0/(1.0+exp(-elem)) : exp(elem)/(1.0+exp(elem));
	    p= max(eps,min(p,1.0-eps));
	    return p;
	});
	return phi;
}

/*VectorXd LogisticRegression::logSigmoid(VectorXd &eta){
	VectorXd phi = eta.unaryExpr([](double elem) // changed type of parameter
	{
	   double p= (elem>0) ?  elem-log(1.0+exp(elem)) : -log(1.0+exp(-elem)) ;
	   return p;
	});
	return phi;
}*/

double LogisticRegression::logLikelihood(){
	ArrayXd y_array=this->Y_train->array();
	ArrayXd phi_array=this->phi.array();
	ArrayXd log_likelihood = y_array*phi_array.log() + ((1.0-y_array)*(1-phi_array).log());
	return log_likelihood.sum();
}

double LogisticRegression::logPrior(){
    double prior = -log(sqrt(2*M_PI))-0.5*log(pow(this->lambda,this->dim))-this->weights.squaredNorm()/(2*this->lambda);
    if(this->with_bias) prior += -log(sqrt(2*M_PI))-log(sqrt(this->lambda))- pow(this->bias,2)/(2*this->lambda);
	return prior;
}

double LogisticRegression::logPosterior(){
	double log_likelihood=logLikelihood();
	double log_prior = logPrior();
    return log_likelihood + log_prior;
}


double LogisticRegression::getGradientBias(){
	return this->grad_bias;
}

/*MatrixXd LogisticRegression::computeHessian(MatrixXd &_X, VectorXd &_Y, VectorXd &_W){
	VectorXd eta = (_X*_W);
	VectorXd YZ=_Y.cwiseProduct(eta);
	VectorXd P=sigmoid(YZ);
	MatrixXd I=MatrixXd::Identity(dim,dim);
	MatrixXd H(dim,dim);
	MatrixXd J(rows,rows);
	J.diagonal() << P.array()*(1-P.array()).array();
	H=_X.transpose()*J;
	H*=_X;
	H+=lambda*I;
	return H.inverse();
}*/

void LogisticRegression::setWeights(VectorXd &_W){
	this->weights=_W;
}

void LogisticRegression::setBias(double bias){
	this->bias=bias;
	this->with_bias = true;
}

VectorXd LogisticRegression::getWeights(){
	return this->weights;
}

double LogisticRegression::getBias(){
	return this->bias;
}

void LogisticRegression::setData(MatrixXd &_X,VectorXd &_Y, bool _preprocesing){
	this->X_train = &_X;
 	this->Y_train = &_Y;
	tools.dataPermutation(*this->X_train,*this->Y_train);
 	this->rows = this->X_train->rows();
	this->dim = this->X_train->cols();
	if(_preprocesing){
 		if(this->normalization) tools.dataNormalization(*this->X_train,this->featureMax,this->featureMin);
 		if(this->standardization) tools.dataStandardization(*this->X_train,this->featureMean,this->featureStd);
 	}
}

void LogisticRegression::saveModel(string name){
	VectorXd weights = this->getWeights();
	VectorXd bias(1);
	bias << this->getBias();
	tools.writeToCSVfile(name+"_Model_weights.csv", weights);
	tools.writeToCSVfile(name+"_Model_means.csv", this->featureMean.transpose());
	tools.writeToCSVfile(name+"_Model_stds.csv", this->featureStd.transpose());
	tools.writeToCSVfile(name+"_Model_maxs.csv", this->featureMax.transpose());
	tools.writeToCSVfile(name+"_Model_mins.csv", this->featureMin.transpose());
	tools.writeToCSVfile(name+"_Model_bias.csv", bias);
}

void LogisticRegression::loadModel(VectorXd weights,VectorXd featureMean, VectorXd featureStd, VectorXd featureMax, VectorXd featureMin, double bias){
	this->init(true, true, true);
	this->setWeights(weights);
	this->setBias(bias);
	this->featureMean = featureMean;
	this->featureStd = featureStd;
	this->featureMax = featureMax;
	this->featureMin = featureMin;
}
